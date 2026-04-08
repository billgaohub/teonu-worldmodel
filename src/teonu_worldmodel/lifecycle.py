"""
NodeLifecycle — 节点生命周期管理器

状态流转：
draft → inferred → confirmed → stable → decayed

核心概念：
- confidence: 置信度（0.0-1.0）
- half_life_days: 半衰期（用于 confidence 衰减）
- last_verified: 最后验证时间
"""

from datetime import datetime, timedelta
from typing import Dict, Any


class NodeLifecycle:
    """节点生命周期管理器"""

    VALID_STATUSES = {"draft", "inferred", "confirmed", "stable", "decayed"}

    STATUS_ORDER = {
        "draft": 0,
        "inferred": 1,
        "confirmed": 2,
        "stable": 3,
        "decayed": 4,
    }

    def __init__(self):
        pass

    def advance_status(
        self,
        node: Dict[str, Any],
        new_status: str,
        trigger: str,
        evidence: str = "",
    ) -> Dict[str, Any]:
        """推进节点状态"""
        if new_status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {new_status}")

        old_status = node["lifecycle"]["status"]
        now = datetime.now().isoformat()

        # 更新状态
        node["lifecycle"]["status"] = new_status
        node["lifecycle"]["last_verified"] = now

        # 状态变化时提升 confidence
        if self.STATUS_ORDER[new_status] > self.STATUS_ORDER[old_status]:
            node["lifecycle"]["confidence"] = min(
                node["lifecycle"]["confidence"] + 0.1, 1.0
            )

        # 记录历史
        node["history"].append({
            "timestamp": now,
            "status": new_status,
            "trigger": trigger,
            "evidence": evidence,
            "confidence": node["lifecycle"]["confidence"],
        })

        node["updated"] = now
        return node

    def verify(
        self,
        node: Dict[str, Any],
        verified_value: Any,
        field: str,
        method: str = "manual",
    ) -> Dict[str, Any]:
        """
        验证节点某字段的实际值
        如果与 inferred 值一致 → 升级为 confirmed
        如果不一致 → 记录 conflict
        """
        current_value = node["state"].get(field)
        now = datetime.now().isoformat()

        if current_value == verified_value:
            # 验证通过
            return self.advance_status(
                node, "confirmed", f"验证通过 (method: {method})", f"{field}={verified_value}"
            )
        else:
            # 验证失败，记录冲突
            node["conflict"] = {
                "status": "active",
                "field": field,
                "values": {
                    "inferred": current_value,
                    "verified": verified_value,
                },
                "resolution": None,
                "detected": now,
            }
            node["updated"] = now
            return node

    def decay_confidence(
        self,
        node: Dict[str, Any],
        days_elapsed: int = None,
    ) -> Dict[str, Any]:
        """
        根据半衰期衰减置信度
        公式：confidence = initial * (0.5 ^ (days / half_life_days))
        """
        half_life = node["lifecycle"].get("half_life_days", 30)
        if days_elapsed is None:
            last_verified = node["lifecycle"].get("last_verified", node["updated"])
            if isinstance(last_verified, str):
                from dateutil.parser import parse
                last_verified = parse(last_verified)
            days_elapsed = (datetime.now() - last_verified).days

        initial_conf = node["lifecycle"].get("confidence", 1.0)
        decayed_conf = initial_conf * (0.5 ** (days_elapsed / half_life))
        node["lifecycle"]["confidence"] = round(decayed_conf, 4)

        # 置信度过低 → decayed 状态
        if decayed_conf < 0.3:
            node["lifecycle"]["status"] = "decayed"

        return node
