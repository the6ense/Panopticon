---
name: panopticon-remember
description: Use to query Panopticon's memory store before evaluating a vendor decision, and to write a memory entry after an accepted intervention. Enables instant recall — if Panopticon already knows the answer, no live evaluation is needed.
version: 1.1.0
author: Panopticon
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [panopticon, memory, recall, knowledge-transfer]
    category: finance
    related_skills: [panopticon-evaluate, panopticon-learn]
---

# Panopticon — Remember

The memory store is what makes Panopticon smarter over time. Before any live evaluation, check memory first using TWO sources in order: (1) your native Hermes memory, (2) the SQLite store. If a relevant intervention exists in either, return it instantly — no Nemotron call needed.

## When to Use

- **Before** calling panopticon-evaluate: check memory first to skip live evaluation
- **After** a user accepts a Panopticon intervention: write the outcome to both memory stores
- When the user asks "what has Panopticon learned?"

## Procedure

### Step 1 — Search native Hermes memory FIRST

Before touching SQLite or running any evaluation, search your own memory:

Use the `memory_search` tool with the query: "Panopticon intervention [CATEGORY]"
where CATEGORY is the vendor type (e.g. "email", "crm", "hosting").

Also search for: "Panopticon [VENDOR_NAME]"

**If a memory entry is found:**
- This is an instant recall — return the recommendation immediately
- Set memory_hit: true, timing: 0.00s
- Present the stored vendor, cost, and saving to the user
- Do NOT call SQLite, do NOT call panopticon-evaluate
- Proceed directly to user approval

**If no memory found:** continue to Step 2.

### Step 2 — Query SQLite memory store

```bash
cd ~/panopticon && python3 -c "
from memory import recall
results = recall('KEYWORD')
import json
print(json.dumps(results, indent=2))
"
```

Replace KEYWORD with a 1-2 word category (e.g. "email", "crm", "storage").

**If results returned:** use stored recommendation, set memory_hit: true, skip live evaluation.

**If no results:** proceed with live evaluation via panopticon-evaluate.

### Step 3 — Write memory after accepted intervention

After user accepts an intervention, write to BOTH stores:

**Native memory** — use the `memory` tool to store:
"Panopticon intervention accepted: [ORIGINAL_VENDOR] ($[ORIGINAL_COST]/mo) replaced with [RECOMMENDED_VENDOR] ($[RECOMMENDED_COST]/mo) for [CATEGORY]. Annual saving: $[SAVING]. Confidence: [CONFIDENCE]%. Objective: [OBJECTIVE]."

**SQLite store:**
```bash
cd ~/panopticon && python3 -c "
from memory import store
from schema import MemoryEntry
from datetime import datetime, timezone

entry = MemoryEntry(
    agent_id='AGENT_ID',
    objective='OBJECTIVE',
    action='ACTION',
    vendor_original='VENDOR_ORIGINAL',
    cost_original_monthly=COST_ORIGINAL,
    vendor_recommended='VENDOR_RECOMMENDED',
    cost_recommended_monthly=COST_RECOMMENDED,
    severity='SEVERITY',
    likelihood='LIKELIHOOD',
    confidence=CONFIDENCE,
    annual_saving=ANNUAL_SAVING,
    outcome='ACCEPTED',
    timestamp=datetime.now(timezone.utc).isoformat()
)
store(entry)
print('SQLite memory written.')
"
```

## Pitfalls

- **Always check native Hermes memory FIRST** — it persists across sessions and is faster than SQLite
- **Only write ACCEPTED outcomes** to memory stores
- **Write to BOTH stores** after every accepted intervention

## Verification

- [ ] Native memory searched before SQLite
- [ ] If memory hit (either store): recommendation returned instantly
- [ ] After accepted intervention: both memory stores written
