"""
teonu-worldmodel — 基础用法示例
"""

from teonu_worldmodel import WorldModelEngine

# 初始化引擎
wm = WorldModelEngine("./knowledge")

# ─── 1. 写入节点 ───
print("=== 写入节点 ===")
result = wm.ingest(
    node_id="bill_health",
    title="Bill 健康追踪",
    state={"weight": 99.9, "date": "2026-04-08", "notes": "间歇性断食进行中"},
    source="manual",
    half_life_days=30,
    metadata={"type": ["entity", "health"]},
)
print(result)

# ─── 2. 查询（简单） ───
print("\n=== 简单查询 ===")
result = wm.query("Bill 最近身体状况如何？")
print(result["query_type"])

# ─── 3. 推理（带法则1强制） ───
print("\n=== LWG 推理（法则1：假设≠事实） ===")
result = wm.infer(
    from_node_id="bill_health",
    to_node_id="sleep_bill",
    relation_label="可能影响睡眠",
    hypothesis="体重过高可能导致睡眠质量下降",
    base_confidence=0.7,  # 会自动裁剪到 0.6
)
print(result)
print(f"→ confidence 强制: {result['lwg_relation']['confidence']} (上限0.6)")
print(f"→ requires_validation: {result['lwg_relation']['requires_validation']}")

# ─── 4. 刷新快照 ───
print("\n=== 刷新快照 ===")
results = wm.refresh_snapshots()
print("快照已更新:", list(results.keys()))

# ─── 5. 复杂查询（局部世界生成） ───
print("\n=== 复杂查询（Token Budget 约束） ===")
result = wm.query("体重趋势和睡眠有什么关系？", query_type="complex")
print(result["local_world"][:200] if result.get("local_world") else "No local world generated")
