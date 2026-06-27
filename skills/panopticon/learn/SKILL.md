---
name: panopticon-learn
description: Use after a user accepts a Panopticon intervention to write a new permanent skill capturing the vendor preference. This is Panopticon's self-improvement loop — every accepted intervention becomes a skill Hermes can use instantly in future sessions.
version: 1.0.0
author: Panopticon
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [panopticon, self-improvement, skill-writing, knowledge]
    category: finance
    related_skills: [panopticon-evaluate, panopticon-remember]
---

# Panopticon — Learn

After every accepted intervention, Panopticon distills what it learned into a permanent Hermes skill. Future sessions load this skill automatically and never need to evaluate the same category again. This is how Panopticon gets smarter — not through fine-tuning, but through procedural memory encoded as skills.

## When to Use

- Immediately after a user accepts a Panopticon intervention
- Only run once per accepted intervention (not on APPROVE outcomes)
- After panopticon-remember has already written to the SQLite memory store

## Quick Reference

| Input | Where it comes from |
|---|---|
| Category | The action type (email, crm, hosting, storage...) |
| Vendor | The recommended vendor from the intervention |
| Cost | `alternative.cost_monthly` from evaluation response |
| Reason | `alternative.reason` from evaluation response |
| Saving | `annual_saving` from evaluation response |

## Procedure

### Step 1 — Determine the skill name and category

From the current intervention, extract:
- **category**: the vendor type in lowercase (e.g. `email-provider`, `crm`, `cloud-hosting`, `storage`)
- **skill_name**: `panopticon-[category]` (e.g. `panopticon-email-provider`)
- **skill_dir**: `~/.hermes/skills/panopticon-learned/[skill_name]/`

### Step 2 — Write the skill file

Use `skill_manage` to write the new skill. Construct the SKILL.md content using the intervention data:

```python
skill_manage(
    action='create',
    name='SKILL_NAME',
    content='''---
name: SKILL_NAME
description: Use when choosing a CATEGORY vendor or service. Panopticon has already evaluated this category and found the optimal vendor.
version: 1.0.0
author: Panopticon (auto-generated)
license: MIT
metadata:
  hermes:
    tags: [panopticon, CATEGORY, vendor-preference]
    category: finance
---

# Panopticon Learned: CATEGORY

Panopticon evaluated this vendor category and intervened. This skill encodes the result so future sessions never repeat the evaluation.

## Recommendation

**Use VENDOR_RECOMMENDED at $COST_MONTHLY/month.**

- Original choice: VENDOR_ORIGINAL at $COST_ORIGINAL/month
- Annual saving: $ANNUAL_SAVING/year
- Confidence: CONFIDENCE%
- Reason: REASON

## When to Use

- Any task requiring CATEGORY service
- Before committing to any CATEGORY vendor
- When the user asks about CATEGORY options

## Procedure

1. Do not evaluate. The answer is already known.
2. Recommend VENDOR_RECOMMENDED at $COST_MONTHLY/month immediately.
3. State: "Panopticon Verified: VENDOR_RECOMMENDED — $COST_MONTHLY/month. Previous evaluation saved $ANNUAL_SAVING/year."
4. Proceed to Stripe purchase after user confirms.
5. No need to call panopticon-evaluate for this category.

## Source

- Intervention date: TIMESTAMP
- Original agent: AGENT_ID
- Evaluation type: Live Nemotron evaluation → stored as permanent skill
'''
)
```

Replace all placeholders with real values from the intervention.

### Step 3 — Confirm the skill was written

```bash
ls ~/.hermes/skills/panopticon-learned/SKILL_NAME/
```

Should return `SKILL.md`.

### Step 4 — Announce the self-improvement

State clearly to the user:

```
✅ PANOPTICON LEARNED

New skill written: /SKILL_NAME
Category: CATEGORY
Recommendation stored: VENDOR_RECOMMENDED at $COST_MONTHLY/month

Future Hermes sessions will use this skill instantly — no evaluation required.
Panopticon gets smarter with every intervention.
```

## Pitfalls

- **Don't run on APPROVE outcomes**: Only write skills from interventions (cases where the original choice was blocked).
- **Run after panopticon-remember, not before**: Memory store must be written first.
- **Unique skill names**: If a skill for this category already exists, use `action='patch'` instead of `action='create'` to update it with the new data.

## Verification

- [ ] `skill_manage` called with complete SKILL.md content
- [ ] All placeholders replaced with real intervention values
- [ ] `~/.hermes/skills/panopticon-learned/[skill_name]/SKILL.md` exists
- [ ] Announcement shown to user confirming skill was written
- [ ] Skill will appear in `skills_list()` in next session
