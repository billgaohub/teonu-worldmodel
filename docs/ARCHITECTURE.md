# Teonu WorldModel Engine — 架构文档

> 本文档详细描述 Teonu WorldModel Engine 的核心架构设计。

---

## 1. 核心定位

**"让 AI 系统具备元认知调度能力"**

三层认知控制：
- **输入控制（Ingest）** — 决定什么能进入世界
- **上下文控制（Snapshot）** — 决定当前看到什么世界
- **推理控制（LWG）** — 决定如何理解世界

---

## 2. 三条系统法则

### 法则1：假设 ≠ 事实

```python
# LWG 生成的推断必须：
# 1. confidence <= 0.6
# 2. requires_validation = True
# 3. 写入 lwg_relations（独立字段）
lwg_relation = {
    "source": "LWG",
    "confidence": min(base_conf, 0.6),
    "requires_validation": True,
    "status": "pending_validation",
}
```

### 法则2：认知必须可压缩

```
触发条件（任一）：
- history > 10 条
- pending 超时
- 节点大小 > 10KB

压缩操作：
- resolved conflict → 合并进 state
- history 摘要化（保留关键节点）
- pending 超时 → 遗忘或升级 alert
- 低置信度 LWG 推断 → 删除
```

### 法则3：上下文受预算约束

```
Token Budget: 2000

优先级排序：
1. stable 状态节点（最高）
2. confirmed 状态节点
3. 高 confidence (>0.7)
4. 近期更新节点

超出预算 → 裁剪 inferred + 低 confidence 节点
```

---

## 3. 模块结构

```
src/teonu_worldmodel/
├── engine.py          # WorldModelEngine 主类
├── ingest.py         # 输入解释层（输入即编译）
├── lifecycle.py      # 节点生命周期
├── compactor.py      # 认知压缩器
├── graph_builder.py   # 关系构建 + 局部世界生成
└── snapshot.py       # 分层快照生成器
```

---

## 4. 节点生命周期

```
draft → inferred → confirmed → stable → decayed
```

| 状态 | 含义 | confidence 范围 |
|------|------|----------------|
| draft | 草稿（未验证） | 0.3–0.6 |
| inferred | LWG 推断（需验证） | 0.4–0.6 |
| confirmed | 已验证 | 0.7–0.9 |
| stable | 稳定（多次验证一致） | 0.85–1.0 |
| decayed | 置信度衰减至失效 | <0.3 |

---

## 5. 分层快照

| 快照文件 | 用途 | 大小约束 |
|----------|------|----------|
| core.md | 核心状态 | <500 tokens |
| recent.md | 最近7天事件 | 无限制 |
| decisions.md | 决策摘要 | 无限制 |
| alerts.md | 冲突/风险 | 无限制 |
| bridges.md | 跨域桥接 | 无限制 |
