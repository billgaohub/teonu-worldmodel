# Teonu WorldModel Engine

> 让 AI 系统具备元认知调度能力的架构引擎 / Architecture Engine for AI Metacognitive Scheduling

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Archived](https://img.shields.io/badge/Status-Arhived-lightgrey.svg)](#)

[中文](README.md) · [English](README_EN.md)

---

## What It Is

Teonu WorldModel Engine is an open-source cognitive architecture engine that gives AI systems the ability to **control how they think** — not just what they know.

> *"The value of a system is not what it knows, but when it changes its own judgment."*

**三大痼疾 vs Teonu 解法 / Three Chronic Problems vs Teonu Solutions:**

| 痼疾 Problem | 解法 Solution |
|---------------|---------------|
| 🔥 **幻觉污染 / Hallucination** — Assumptions treated as facts | **法则1：假设≠事实 / Assumption ≠ Fact** — LWG inferences must be marked for verification |
| 🗑️ **熵增失控 / Entropy Overflow** — Knowledge堆积 unbounded | **法则2：认知必须可压缩 / Cognition Must Be Compressible** — forget/merge/summarize |
| 💥 **上下文膨胀 / Context Explosion** — Token budget burst | **法则3：上下文受预算约束 / Context Has Budget** — dynamic pruning |

---

## Three-Layer Cognitive Control

```
User Query
    │
    ├─── 输入控制 / Ingest ──────► 决定什么能进入世界
    │
    ├─── 上下文控制 / Snapshot ──► 决定当前看到什么世界
    │
    └─── 推理控制 / LWG ─────────► 决定如何理解世界
                    │
                    ▼
        认知不是自由的，是被调度的
    Cognition is not free — it is scheduled
```

---

## Quick Start

```bash
pip install teonu-worldmodel

from teonu_worldmodel import WorldModelEngine

wm = WorldModelEngine("/path/to/knowledge/")
wm.ingest("user_query", source_data={"content": "...", "source": "journal"})
result = wm.query("最近的身体状况如何？")
print(result)
```

---

## Core Concept: Node

Knowledge unit with lifecycle:

```yaml
id: bill_health
title: Bill 健康追踪 / Bill Health Tracker
state:
  weight: 99.9
  date: 2026-04-08
lifecycle:
  status: stable          # draft → inferred → confirmed → stable → decayed
  confidence: 0.95
  half_life_days: 30
```

---

## Three System Laws

```python
# Law 1: Assumption ≠ Fact
# LWG inferences must have confidence <= 0.6, marked requires_validation

# Law 2: Cognition Must Be Compressible
# > 10 history items → auto-summarize
# pending timeout → auto-forget or escalate to alert

# Law 3: Context Has Hard Budget
# Token budget 2000; when exceeded, preserve stable + high-confidence nodes first
```

---

## Architecture

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
├── README.md / README_EN.md
└── LICENSE
```

---

## Use Cases / 适用场景

- **个人 AI 助手 / Personal AI Assistant** — 记忆、可追溯、自我修正
- **企业知识库 / Enterprise Knowledge Base** — 防知识污染，保证可信度
- **AI Agent** — 安装认知刹车，防止失控推断
- **决策支持系统 / Decision Support** — 建议可追溯、可解释、可反转

---

## Origin

Derived from **SONUV** system — L3 WorldModel Layer practice.

> *"If you care about cognitive quality, not just cognitive quantity, Teonu WorldModel is your engine."*

---

## Status

⚠️ **Archived** — Merged into [AI Governance Framework](https://github.com/billgaohub/AIUCE)

---

## License

MIT License · See [LICENSE](LICENSE)
