# ⚠️ 已归档

> 本项目已归档，内容合并至 [AI Governance Framework](https://github.com/billgaohub/AIUCE)。
> 
> 新的文件整理工具：[IPIPQ](https://github.com/billgaohub/ipipq)

---

# Teonu WorldModel Engine

> 让 AI 系统具备"元认知调度"能力的架构引擎

[English README](README_EN.md)

---

## 核心定位

**"系统的价值不在于它知道什么，而在于它在什么时候改变了自己的判断。"**

Teonu WorldModel Engine 是一个开源的 AI 认知架构引擎，专注于解决 AI 系统的三大痼疾：

| 痼疾 | Teonu 解法 |
|------|-----------|
| 🔥 **幻觉污染** — 假设直接当事实 | **法则1：假设≠事实**（LWG 推断必须标记验证） |
| 🗑️ **熵增失控** — 知识无限堆积 | **法则2：认知必须可压缩**（遗忘/合并/摘要） |
| 💥 **上下文膨胀** — token 预算爆炸 | **法则3：上下文受预算约束**（动态裁剪） |

> 从 *"能思考的系统"* → **"能控制自己如何思考的系统"**

---

## 三层认知控制

```
用户 Query
    │
    ├─── 输入控制（Ingest）─────► 决定什么能进入世界
    │
    ├─── 上下文控制（Snapshot）──► 决定当前看到什么世界
    │
    └─── 推理控制（LWG）────────► 决定如何理解世界
                    │
                    ▼
            认知不是自由的，是被调度的
```

---

## 快速开始

```bash
pip install teonu-worldmodel

# 基本使用
from teonu_worldmodel import WorldModelEngine

wm = WorldModelEngine("/path/to/knowledge/")
wm.ingest("user_query", source_data={"content": "...", "source": "journal"})
result = wm.query("最近的身体状况如何？")
print(result)
```

---

## 核心概念

### 节点（Node）

知识的基本单元，带生命周期：

```yaml
id: bill_health
title: Bill 健康追踪
state:
  weight: 99.9
  date: 2026-04-08
lifecycle:
  status: stable          # draft → inferred → confirmed → stable → decayed
  confidence: 0.95
  half_life_days: 30
```

### 三条系统法则

```python
# 法则1：假设不得直接成为事实
# LWG 生成的推断必须 confidence <= 0.6，必须标记 requires_validation

# 法则2：认知必须可压缩
# 超过 10 条 history → 自动摘要化
# pending 超时 → 自动遗忘或升级为 alert

# 法则3：上下文必须受预算约束
# token budget 2000，超限时优先保留 stable + 高 confidence 节点
```

### 分层快照

```
snapshot/
├── core.md        # 核心状态（永远小，<500 tokens）
├── recent.md      # 最近 7 天事件
├── decisions.md   # 决策摘要
├── alerts.md      # 冲突 / 风险
└── bridges.md     # 跨域桥接（防语义割裂）
```

---

## 目录结构

```
teonu-worldmodel/
├── src/teonu_worldmodel/
│   ├── __init__.py
│   ├── engine.py         # WorldModelEngine 主类
│   ├── ingest.py         # 输入解释层
│   ├── lifecycle.py      # 节点生命周期
│   ├── compactor.py      # 认知压缩器
│   ├── graph_builder.py  # 关系构建 + 局部世界生成
│   └── snapshot.py       # 分层快照
├── docs/
│   └── ARCHITECTURE.md
├── examples/
│   ├── basic_usage.py
│   └── advanced_usage.py
├── tests/
│   └── test_engine.py
├── README.md
├── README_EN.md
├── LICENSE
└── requirements.txt
```

---

## 适用场景

- **个人 AI 助手**：构建有记忆、可追溯、自我修正的 AI 助理
- **企业知识库**：防止知识污染，保证知识可信度
- **AI Agent**：给 Agent 安装"认知刹车"，防止失控推断
- **决策支持系统**：保证每个建议可追溯、可解释、可反转

---

## 设计背景

本项目源于 [SONUV](https://github.com/billgaohub/AIUCE) 系统（一个十一层架构的个人 AI 治理框架）的 L3 世界模型层实践。

> 如果你关心 AI 系统的"认知质量"而非仅仅"认知数量"，Teonu WorldModel 是为你准备的。

---

## License

MIT License — 详见 [LICENSE](LICENSE)
