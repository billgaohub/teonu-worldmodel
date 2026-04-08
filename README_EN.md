# Teonu WorldModel Engine

> An architectural engine that gives AI systems metacognitive control over their own cognition.

---

## Core Positioning

*"The value of a system is not what it knows, but when it changes its own judgment."*

Teonu WorldModel Engine addresses three fundamental problems in AI systems:

| Problem | Teonu Solution |
|---------|---------------|
| 🔥 **Hallucination Pollution** | **Law 1: Hypothesis ≠ Fact** (LWG inferences must be marked for validation) |
| 🗑️ **Entropy Overflow** | **Law 2: Cognition Must Be Compressible** (forget/merge/summarize) |
| 💥 **Context Explosion** | **Law 3: Context Within Budget** (dynamic pruning) |

> From *"system that can think"* → **"system that controls how it thinks"**

---

## Quick Start

```bash
pip install teonu-worldmodel

from teonu_worldmodel import WorldModelEngine

wm = WorldModelEngine("/path/to/knowledge/")
wm.ingest("user_feedback", source_data={"content": "...", "source": "diary"})
result = wm.query("How is my health recently?")
print(result)
```

---

## Three Laws of System

```python
# Law 1: Hypothesis ≠ Fact
# LWG-generated inferences must confidence <= 0.6, must require_validation

# Law 2: Cognition Must Be Compressible
# > 10 history entries → auto-summarize
# Pending timeout → auto-forget or upgrade to alert

# Law 3: Context Within Budget
# Token budget 2000, prune inferred + low-confidence nodes first
```

---

## Architecture

```
Query → Ingest (Input Control) → Snapshot (Context Control) → LWG (Reasoning Control)
                          ↓
        Cognition is not free — it is scheduled.
```

---

## License

MIT License — see [LICENSE](LICENSE)
