"""
WorldModelEngine — Teonu WorldModel 核心引擎

核心设计：
- 三层认知控制：输入控制 → 上下文控制 → 推理控制
- 三条系统法则：假设≠事实 / 认知可压缩 / 上下文受预算
"""

import os
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any
from .lifecycle import NodeLifecycle
from .compactor import NodeCompactor
from .snapshot import SnapshotGenerator
from .graph_builder import GraphBuilder


class WorldModelEngine:
    """
    世界模型引擎
    核心功能：
    - ingest(): 输入控制，决定什么能进入世界
    - query(): 上下文控制，决定当前看到什么世界
    - infer(): 推理控制，决定如何理解世界（含 LWG 限制）
    """

    TOKEN_BUDGET = 2000  # 局部世界生成 token 上限

    def __init__(self, root_path: str, token_budget: int = 2000):
        self.root_path = Path(root_path)
        self.token_budget = token_budget
        self.nodes_dir = self.root_path / "nodes"
        self.snapshot_dir = self.root_path / "snapshot"
        self._ensure_dirs()
        self.lifecycle = NodeLifecycle()
        self.compactor = NodeCompactor()
        self.snapshot_gen = SnapshotGenerator(str(self.snapshot_dir))
        self.graph = GraphBuilder(str(self.nodes_dir))
        self._index = self._load_index()

    def _ensure_dirs(self):
        """确保目录结构存在"""
        self.nodes_dir.mkdir(parents=True, exist_ok=True)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    def _load_index(self) -> Dict[str, Any]:
        """加载节点索引"""
        idx_file = self.root_path / "index.json"
        if idx_file.exists():
            return json.loads(idx_file.read_text())
        return {"nodes": {}, "updated": None}

    def _save_index(self):
        """保存节点索引"""
        self._index["updated"] = datetime.now().isoformat()
        (self.root_path / "index.json").write_text(
            json.dumps(self._index, ensure_ascii=False, indent=2)
        )

    # ─── 输入控制 ───
    def ingest(
        self,
        node_id: str,
        title: str,
        state: Dict[str, Any],
        source: str = "manual",
        half_life_days: int = 30,
        metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        输入控制：决定什么能进入世界

        Args:
            node_id: 节点唯一标识
            title: 节点标题
            state: 当前状态数据
            source: 数据来源 (manual/llm/sensor/api)
            half_life_days: 半衰期（天），用于 confidence 衰减
            metadata: 附加元数据

        Returns:
            节点创建/更新结果
        """
        node_path = self.nodes_dir / f"{node_id}.yaml"

        if node_path.exists():
            # 更新现有节点
            node = yaml.safe_load(node_path.read_text())
            node["state"] = state
            node["updated"] = datetime.now().isoformat()
            node["history"].append({
                "timestamp": datetime.now().isoformat(),
                "action": "state_updated",
                "source": source,
                "old_state": node.get("state"),
                "new_state": state,
            })
        else:
            # 新建节点
            now = datetime.now().isoformat()
            node = {
                "id": node_id,
                "title": title,
                "type": metadata.get("type", ["entity"]) if metadata else ["entity"],
                "state": state,
                "lifecycle": {
                    "status": "confirmed" if source == "manual" else "draft",
                    "confidence": 1.0 if source == "manual" else 0.7,
                    "source": source,
                    "half_life_days": half_life_days,
                    "created": now,
                    "last_verified": now,
                },
                "version": 1,
                "history": [
                    {
                        "timestamp": now,
                        "status": "draft" if source != "manual" else "confirmed",
                        "trigger": f"首次记录 (source: {source})",
                    }
                ],
                "lwg_relations": [],
                "pending": [],
                "conflict": {"status": None, "field": None, "values": {}, "resolution": None},
                "compaction": {
                    "last_compact": None,
                    "compact_count": 0,
                    "original_history_size": 0,
                },
            }
            if metadata:
                node["metadata"] = metadata

        # 持久化
        node_path.write_text(yaml.dump(node, allow_unicode=True, sort_keys=False))
        self._index["nodes"][node_id] = {
            "path": str(node_path),
            "updated": node.get("updated", datetime.now().isoformat()),
            "status": node["lifecycle"]["status"],
        }
        self._save_index()
        return {"success": True, "node_id": node_id, "status": node["lifecycle"]["status"]}

    # ─── 上下文控制 ───
    def query(
        self,
        query_text: str,
        query_type: str = "auto",
        include_bridges: bool = True,
    ) -> Dict[str, Any]:
        """
        上下文控制：决定当前看到什么世界

        查询类型路由：
        - simple: 只加载 core snapshot
        - trend: core + recent
        - decision: core + decisions + constraints
        - cross_domain: core + bridges（跨域查询）
        - complex: 局部世界生成（含 token budget 约束）
        - auto: 自动判断
        """
        if query_type == "auto":
            query_type = self._route_query(query_text)

        # 加载相关 snapshot
        snapshots = {}
        for name in ["core", "recent", "decisions", "alerts"]:
            path = self.snapshot_dir / f"{name}.md"
            if path.exists():
                snapshots[name] = path.read_text()

        if include_bridges:
            bridges_path = self.snapshot_dir / "bridges.md"
            if bridges_path.exists():
                snapshots["bridges"] = bridges_path.read_text()

        # 复杂查询 → 局部世界生成
        if query_type == "complex":
            local_world = self.graph.generate_local_world(
                query_text, budget=self.token_budget
            )
            return {
                "query_type": query_type,
                "snapshots": snapshots,
                "local_world": local_world,
                "token_budget_used": self.token_budget,
            }

        return {"query_type": query_type, "snapshots": snapshots}

    def _route_query(self, query_text: str) -> str:
        """根据查询文本自动判断查询类型"""
        text = query_text.lower()
        if any(k in text for k in ["趋势", "变化", "最近", "怎么样", "how", "trend", "recent"]):
            return "trend"
        if any(k in text for k in ["决策", "决定", "选择", "要不要", "decision", "choose"]):
            return "decision"
        if any(k in text for k in ["影响", "关系", "connection", "affect"]):
            return "cross_domain"
        if len(query_text) > 50:
            return "complex"
        return "simple"

    # ─── 推理控制 ───
    def infer(
        self,
        from_node_id: str,
        to_node_id: str,
        relation_label: str,
        hypothesis: str,
        base_confidence: float = 0.5,
    ) -> Dict[str, Any]:
        """
        推理控制：LWG 局部世界生成

        ⚠️ 强制执行法则1：假设 ≠ 事实
        - confidence 强制 <= 0.6
        - 必须标记 requires_validation = True
        - 写入 lwg_relations（独立字段），不污染 relations
        """
        # 法则1 强制：confidence 上限 0.6
        confidence = min(base_confidence, 0.6)

        node_path = self.nodes_dir / f"{from_node_id}.yaml"
        if not node_path.exists():
            return {"success": False, "error": f"Node {from_node_id} not found"}

        node = yaml.safe_load(node_path.read_text())

        # 构建 LWG 关系（带强制标记）
        lwg_relation = {
            "to": to_node_id,
            "label": relation_label,
            "hypothesis": hypothesis,
            "confidence": confidence,
            "source": "LWG",
            "requires_validation": True,
            "created": datetime.now().isoformat(),
            "status": "pending_validation",
        }

        # 写入独立字段，不污染主 state
        if "lwg_relations" not in node:
            node["lwg_relations"] = []
        node["lwg_relations"].append(lwg_relation)
        node["updated"] = datetime.now().isoformat()

        node_path.write_text(yaml.dump(node, allow_unicode=True, sort_keys=False))

        return {
            "success": True,
            "node_id": from_node_id,
            "lwg_relation": lwg_relation,
            "law_compliance": "Law 1: Hypothesis ≠ Fact — requires_validation=True",
        }

    # ─── 快照管理 ───
    def refresh_snapshots(self) -> Dict[str, Any]:
        """刷新所有分层快照"""
        results = {}
        results["core"] = self.snapshot_gen.generate_core(str(self.nodes_dir))
        results["recent"] = self.snapshot_gen.generate_recent(str(self.nodes_dir))
        results["decisions"] = self.snapshot_gen.generate_decisions(str(self.nodes_dir))
        results["alerts"] = self.snapshot_gen.generate_alerts(str(self.nodes_dir))
        if self.graph.bridges_enabled:
            results["bridges"] = self.snapshot_gen.generate_bridges(str(self.nodes_dir))
        return results

    # ─── 认知压缩 ───
    def compact_all(self) -> Dict[str, int]:
        """对所有节点执行认知压缩"""
        compacted = 0
        for node_file in self.nodes_dir.glob("*.yaml"):
            node = yaml.safe_load(node_file.read_text())
            original_size = len(node.get("history", []))
            compacted_node = self.compactor.compact(node)
            if compacted_node != node:
                node_file.write_text(
                    yaml.dump(compacted_node, allow_unicode=True, sort_keys=False)
                )
                compacted += 1
        return {"compacted_nodes": compacted}
