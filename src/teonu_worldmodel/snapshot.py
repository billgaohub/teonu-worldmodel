"""
SnapshotGenerator — 分层快照生成器

生成分层快照：
- core.md: 核心状态（永远小，<500 tokens）
- recent.md: 最近 7 天事件
- decisions.md: 决策摘要
- alerts.md: 冲突 / 风险
- bridges.md: 跨域桥接（防语义割裂）
"""

import os
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List


class SnapshotGenerator:
    """生成分层快照"""

    def __init__(self, snapshot_dir: str):
        self.snapshot_dir = Path(snapshot_dir)

    def generate_core(self, nodes_dir: str) -> str:
        """
        生成核心快照（core.md）
        原则：永远小，<500 tokens
        只包含：stable 状态节点 + 最新验证数据
        """
        lines = ["# 核心状态快照 (Core Snapshot)", "", "> 自动生成，请勿手动修改", ""]
        nodes_added = 0
        total_chars = 0

        for node_file in Path(nodes_dir).glob("*.yaml"):
            if total_chars > 3000:  # ~500 tokens
                break
            try:
                node = yaml.safe_load(node_file.read_text())
                status = node.get("lifecycle", {}).get("status")

                if status in ("stable", "confirmed"):
                    title = node.get("title", node["id"])
                    state = node.get("state", {})
                    conf = node.get("lifecycle", {}).get("confidence", 0)

                    lines.append(f"## {title} (conf={conf:.0%})")
                    for k, v in list(state.items())[:5]:  # 最多5个字段
                        lines.append(f"- {k}: {v}")
                    lines.append("")

                    nodes_added += 1
                    total_chars += sum(len(l) for l in lines[-10:])
            except Exception:
                continue

        lines.append(f"*共 {nodes_added} 个 stable 节点 | 生成时间: {datetime.now().isoformat()}*")
        content = "\n".join(lines)
        (self.snapshot_dir / "core.md").write_text(content)
        return content

    def generate_recent(self, nodes_dir: str, days: int = 7) -> str:
        """生成最近事件快照（recent.md）"""
        lines = [f"# 最近 {days} 天事件快照", "", "> 自动生成", ""]
        cutoff = datetime.now() - timedelta(days=days)
        count = 0

        for node_file in Path(nodes_dir).glob("*.yaml"):
            try:
                node = yaml.safe_load(node_file.read_text())
                for h in node.get("history", []):
                    ts = h.get("timestamp", "")
                    if isinstance(ts, str) and ts:
                        from dateutil.parser import parse
                        try:
                            event_time = parse(ts)
                            if event_time >= cutoff:
                                status_icon = {"stable": "🟢", "confirmed": "🟡", "inferred": "🔵"}.get(
                                    h.get("status", ""), "⚪"
                                )
                                lines.append(
                                    f"- {status_icon} [{ts[:10]}] **{node['title']}**: {h.get('trigger', '')}"
                                )
                                count += 1
                        except Exception:
                            continue
            except Exception:
                continue

        lines.append("")
        lines.append(f"*共 {count} 条近期事件 | 生成时间: {datetime.now().isoformat()}*")
        content = "\n".join(lines)
        (self.snapshot_dir / "recent.md").write_text(content)
        return content

    def generate_decisions(self, nodes_dir: str) -> str:
        """生成决策快照（decisions.md）"""
        lines = ["# 决策摘要快照", "", "> 自动生成 | 仅包含 decision 类型节点", ""]

        for node_file in Path(nodes_dir).glob("*.yaml"):
            try:
                node = yaml.safe_load(node_file.read_text())
                if "decision" in node.get("type", []):
                    title = node.get("title", node["id"])
                    state = node.get("state", {})
                    status = node.get("lifecycle", {}).get("status")
                    lines.append(f"## {title} `{status}`")
                    for k, v in state.items():
                        lines.append(f"- {k}: {v}")
                    lines.append("")
            except Exception:
                continue

        lines.append(f"*生成时间: {datetime.now().isoformat()}*")
        content = "\n".join(lines)
        (self.snapshot_dir / "decisions.md").write_text(content)
        return content

    def generate_alerts(self, nodes_dir: str) -> str:
        """生成告警快照（alerts.md）"""
        lines = ["# 风险告警快照", "", "> 自动生成 | 高置信度冲突或待验证推断", ""]
        count = 0

        for node_file in Path(nodes_dir).glob("*.yaml"):
            try:
                node = yaml.safe_load(node_file.read_text())

                # Active conflict
                conflict = node.get("conflict", {})
                if conflict.get("status") == "active":
                    lines.append(f"⚠️ **冲突** [{node['title']}]:")
                    lines.append(f"  - 字段: `{conflict.get('field')}`")
                    lines.append(f"  - 推断值: `{conflict.get('values', {}).get('inferred')}`")
                    lines.append(f"  - 验证值: `{conflict.get('values', {}).get('verified')}`")
                    lines.append("")
                    count += 1

                # Low confidence stable nodes
                conf = node.get("lifecycle", {}).get("confidence", 1.0)
                status = node.get("lifecycle", {}).get("status")
                if status == "stable" and conf < 0.5:
                    lines.append(f"🔵 **低置信度** [{node['title']}]: conf={conf:.0%}")
                    count += 1

            except Exception:
                continue

        if count == 0:
            lines.append("✅ 无活跃告警")

        lines.append("")
        lines.append(f"*生成时间: {datetime.now().isoformat()}*")
        content = "\n".join(lines)
        (self.snapshot_dir / "alerts.md").write_text(content)
        return content

    def generate_bridges(self, nodes_dir: str) -> str:
        """生成跨域桥接快照（bridges.md）— 防止模块化导致语义割裂"""
        bridges = []
        lines = ["# 跨域桥接快照 (Cross-Domain Bridges)", "", "> 自动生成 | 防止模块化认知断裂", ""]

        # 收集所有节点
        nodes = {}
        for node_file in Path(nodes_dir).glob("*.yaml"):
            try:
                node = yaml.safe_load(node_file.read_text())
                nodes[node["id"]] = node
            except Exception:
                continue

        # 检测跨域关系（简化版：基于关系字段）
        for node_id, node in nodes.items():
            for rel in node.get("lwg_relations", []):
                if rel.get("requires_validation") and rel.get("confidence", 0) >= 0.5:
                    bridges.append({
                        "from": node_id,
                        "to": rel["to"],
                        "label": rel.get("label", ""),
                        "confidence": rel.get("confidence", 0),
                        "type": "LWG_inference",
                    })

        if bridges:
            lines.append("## LWG 跨域推断（需验证）")
            lines.append("")
            lines.append("| 源节点 | 目标 | 关系 | 置信度 |")
            lines.append("|--------|------|------|--------|")
            for b in bridges[:10]:
                conf_bar = "█" * int(b["confidence"] * 10)
                lines.append(
                    f"| `{b['from']}` | `{b['to']}` | {b['label']} | {conf_bar} {b['confidence']:.0%} |"
                )
            lines.append("")
        else:
            lines.append("✅ 无跨域推断")

        lines.append(f"*生成时间: {datetime.now().isoformat()}*")
        content = "\n".join(lines)
        (self.snapshot_dir / "bridges.md").write_text(content)
        return content
