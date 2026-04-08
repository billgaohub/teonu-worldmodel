"""
GraphBuilder — 关系构建 + 局部世界生成

法则3 实现：上下文必须受预算约束

核心功能：
- 在 token budget 内动态裁剪候选节点
- 优先保留：stable 状态 > 高 confidence > 近期更新
- 生成问题专属局部世界（Local World Generation, LWG）
"""

import os
import yaml
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class GraphBuilder:
    """
    关系构建 + 局部世界生成
    遵守法则3：上下文必须受预算约束
    """

    TOKEN_BUDGET = 2000  # 默认 token 上限
    STATUS_PRIORITY = {"stable": 0, "confirmed": 1, "inferred": 2, "draft": 3, "decayed": 4}

    def __init__(self, nodes_dir: str, bridges_enabled: bool = True):
        self.nodes_dir = Path(nodes_dir)
        self.bridges_enabled = bridges_enabled

    def estimate_tokens(self, text: str) -> int:
        """估算文本的 token 数量（粗略估计：中文≈2字符/token，英文≈4字符/token）"""
        if not text:
            return 0
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        english_chars = len(re.findall(r"[a-zA-Z]", text))
        other_chars = len(text) - chinese_chars - english_chars
        return int(chinese_chars / 2 + english_chars / 4 + other_chars / 3)

    def generate_local_world(
        self,
        query: str,
        budget: int = TOKEN_BUDGET,
        max_nodes: int = 20,
    ) -> str:
        """
        生成问题专属局部世界

        法则3 实现：
        1. 在 budget 内动态组装节点
        2. 优先 stable + 高 confidence 节点
        3. 超出预算时，低 confidence / inferred 节点首先被裁剪
        """
        # 1. 找出所有候选节点
        candidates = self._find_candidates(query)

        # 2. 按优先级排序
        candidates.sort(
            key=lambda n: (
                self.STATUS_PRIORITY.get(n["lifecycle"]["status"], 99),
                -n["lifecycle"].get("confidence", 0),
            )
        )

        # 3. 在 budget 内组装
        selected = []
        current_tokens = 0
        pruned_nodes = []

        for node in candidates:
            if len(selected) >= max_nodes:
                pruned_nodes.append(node["id"])
                continue

            node_text = yaml.dump(node, allow_unicode=True, sort_keys=False)
            node_tokens = self.estimate_tokens(node_text)

            if current_tokens + node_tokens <= budget:
                selected.append(node)
                current_tokens += node_tokens
            else:
                # 预算不足，停止添加
                pruned_nodes.append(node["id"])

        # 4. 渲染局部世界
        return self._render_local_world(query, selected, current_tokens, budget, pruned_nodes)

    def _find_candidates(self, query: str) -> List[Dict[str, Any]]:
        """根据查询关键词找到相关候选节点"""
        candidates = []
        keywords = [w.strip() for w in re.split(r"[\s,，。、]", query) if w.strip()]

        for node_file in self.nodes_dir.glob("*.yaml"):
            try:
                node = yaml.safe_load(node_file.read_text())
                node_text = yaml.dump(node, allow_unicode=True)

                # 匹配度：节点标题/内容含查询关键词
                if any(kw in node.get("title", "") or kw in node_text for kw in keywords):
                    candidates.append(node)
            except Exception:
                continue

        # 如果没有匹配，返回最近的 stable 节点
        if not candidates:
            for node_file in self.nodes_dir.glob("*.yaml"):
                try:
                    node = yaml.safe_load(node_file.read_text())
                    if node.get("lifecycle", {}).get("status") == "stable":
                        candidates.append(node)
                        if len(candidates) >= 5:
                            break
                except Exception:
                    continue

        return candidates

    def _render_local_world(
        self,
        query: str,
        selected: List[Dict],
        tokens_used: int,
        budget: int,
        pruned: List[str],
    ) -> str:
        """将选中的节点渲染为局部世界 Markdown"""
        lines = [
            f"# 局部世界（Local World）",
            f"",
            f"> **Query**: {query}",
            f"> **Token Budget**: {tokens_used}/{budget} used",
            f"> **Nodes Selected**: {len(selected)}",
            f">",
        ]

        if pruned:
            lines.append(f"> ⚠️ **Pruned** ({len(pruned)} nodes exceeded budget): `{', '.join(pruned[:5])}{'...' if len(pruned) > 5 else ''}`")
            lines.append(">")
            lines.append("> **裁剪策略**: inferred + 低 confidence 节点优先被移除")

        lines.append("---")
        lines.append("")

        for node in selected:
            status = node["lifecycle"]["status"]
            conf = node["lifecycle"].get("confidence", 0)
            conf_bar = "█" * int(conf * 10) + "░" * (10 - int(conf * 10))

            status_icon = {
                "stable": "🟢",
                "confirmed": "🟡",
                "inferred": "🔵",
                "draft": "⚪",
                "decayed": "⚫",
            }.get(status, "⚪")

            lines.append(f"## {status_icon} {node['title']} `{status}` {conf_bar} {conf:.0%}")
            lines.append("")

            # 渲染 state
            state = node.get("state", {})
            if state:
                lines.append("**State:**")
                for k, v in state.items():
                    lines.append(f"- **{k}**: {v}")
                lines.append("")

            # 渲染 active conflict
            conflict = node.get("conflict", {})
            if conflict.get("status") == "active":
                lines.append("⚠️ **Conflict:**")
                lines.append(f"- field: `{conflict.get('field')}`")
                lines.append(f"- inferred: `{conflict.get('values', {}).get('inferred')}`")
                lines.append(f"- verified: `{conflict.get('values', {}).get('verified')}`")
                lines.append("")

            # 渲染待验证的 LWG relations
            lwg_rels = node.get("lwg_relations", [])
            pending_lwg = [r for r in lwg_rels if r.get("requires_validation") == True]
            if pending_lwg:
                lines.append(f"🔍 **Pending LWG Inferences** ({len(pending_lwg)}):")
                for rel in pending_lwg[:3]:
                    lines.append(f"- → `{rel['to']}`: {rel.get('label', '')} (conf={rel.get('confidence', 0):.0%}) ⚠️ 需验证")
                lines.append("")

        lines.append("---")
        lines.append(f"*Generated at {datetime.now().isoformat()}*")

        return "\n".join(lines)
