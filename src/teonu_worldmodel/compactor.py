"""
NodeCompactor — 认知压缩器

法则2 实现：认知必须可压缩

触发条件（满足任一）：
1. 每天凌晨定时
2. history 超过 10 条
3. 节点大小超过 10KB
4. pending 超时
"""

from datetime import datetime
from typing import Dict, Any, List


class NodeCompactor:
    """
    认知压缩器
    防止节点成为"认知垃圾场"
    """

    HISTORY_THRESHOLD = 10
    NODE_SIZE_KB = 10

    def compact(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行认知压缩
        返回压缩后的节点（如果无变化则返回原节点）
        """
        original = node.copy()
        now = datetime.now().isoformat()

        # 1. 已解决的 conflict → 合并进 state
        if node.get("conflict", {}).get("status") == "resolved":
            field = node["conflict"]["field"]
            resolution = node["conflict"]["resolution"]
            if field and resolution:
                node["state"][field] = resolution
            node["conflict"] = {"status": "merged", "merged_at": now}

        # 2. history 超过阈值 → 摘要化
        history = node.get("history", [])
        if len(history) > self.HISTORY_THRESHOLD:
            node["history"] = self._summarize_history(history)
            node["compaction"]["last_compact"] = now
            node["compaction"]["compact_count"] += 1
            node["compaction"]["original_history_size"] = len(history)

        # 3. pending 超时 → 遗忘或升级
        pending_to_remove = []
        for pending in node.get("pending", []):
            timeout = pending.get("timeout")
            if timeout:
                if isinstance(timeout, str):
                    from dateutil.parser import parse
                    timeout_dt = parse(timeout)
                else:
                    timeout_dt = timeout

                if datetime.now() > timeout_dt:
                    if pending.get("critical", False):
                        # 升级为 alert（通过 snapshot 机制处理）
                        pending["status"] = "upgraded_to_alert"
                    else:
                        pending_to_remove.append(pending)

        for p in pending_to_remove:
            node["pending"].remove(p)

        # 4. LWG relations 验证超时 → 删除低置信度假设
        if "lwg_relations" in node:
            node["lwg_relations"] = [
                rel
                for rel in node["lwg_relations"]
                if not (
                    rel.get("requires_validation") == "expired"
                    and rel.get("confidence", 1.0) < 0.4
                )
            ]

        return node

    def _summarize_history(self, history: List[Dict]) -> List[Dict]:
        """
        摘要化 history
        保留策略：
        - 保留：首次记录、状态变化节点、关键验证
        - 合并：连续相似状态（如多个 stable）
        """
        if not history:
            return history

        summary = []
        last_kept = None

        # 保留首次记录
        summary.append(history[0])
        last_kept = history[0]

        # 遍历后续记录
        for i, h in enumerate(history[1:], 1):
            status = h.get("status", "unknown")

            # 关键状态变化总是保留
            if status != last_kept.get("status"):
                summary.append(h)
                last_kept = h
                continue

            # 关键触发总是保留
            trigger = h.get("trigger", "")
            if any(k in trigger for k in ["人工确认", "复查验证", "验证通过"]):
                summary.append(h)
                last_kept = h
                continue

        # 添加摘要标记
        summary.append({
            "type": "compaction_summary",
            "original_count": len(history),
            "compressed_count": len(summary),
            "compacted_at": datetime.now().isoformat(),
            "note": "连续相似状态已合并，关键节点已保留",
        })

        return summary
