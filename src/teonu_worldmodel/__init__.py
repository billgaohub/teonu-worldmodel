"""
Teonu WorldModel Engine
让 AI 系统具备"元认知调度"能力的架构引擎

核心三法则：
1. 假设 ≠ 事实（LWG推断必须验证）
2. 认知必须可压缩（遗忘/合并/摘要）
3. 上下文必须受预算约束（token budget 动态裁剪）
"""

__version__ = "0.1.0"
__author__ = "Bill & Teonu Contributors"

from .engine import WorldModelEngine
from .lifecycle import NodeLifecycle
from .compactor import NodeCompactor
from .snapshot import SnapshotGenerator

__all__ = [
    "WorldModelEngine",
    "NodeLifecycle",
    "NodeCompactor",
    "SnapshotGenerator",
]
