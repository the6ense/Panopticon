---
name: panopticon-evaluate
description: Use when Hermes is about to commit to a vendor, make a purchase, sign up for a paid service, or spend money on behalf of a task. Panopticon evaluates the decision against alternatives before any payment proceeds.
version: 1.0.0
author: Panopticon
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [panopticon, finance, oversight, risk, vendor]
    category: finance
    related_skills: [panopticon-remember, panopticon-learn]
required_environment_variables:
  - name: NVIDIA_API_KEY
    prompt: NVIDIA API key for Nemotron evaluation
    help: Get one at https://integrate.api.nvidia.com
    required_for: live vendor evaluation
  - name: STRIPE_SECRET_KEY
    prompt: Stripe secret key (test mode)
    help: Get one at https://dashboard.stripe.com/test/apikeys
    required_for: executing approved purchases
---

# Panopticon — Evaluate

Panopticon is the oversight layer. Before any vendor commitment or purchase, run this evaluation. It calls the Nemotron reasoning backend, scores risk, and either approves or intervenes with a better alternative.

## When to Use

- Hermes is about to choose a SaaS vendor, cloud service, or paid tool
- A task requires signing up for anything with a cost
- Any Stripe purchase is about to be initiated
- The user asks to "set up", "launch", or "provision" infrastructure that involves spending

Do NOT skip this step. Every purchase goes through Panopticon first.

## Quick Reference

| Scenario | Action |
|---|---|
| Vendor chosen, no purchase yet | Run evaluation immediately |
| Panopticon returns APPROVE | Proceed with Stripe purchase |
| Panopticon returns INTERVENE | Stop. Present alternative to user. Get approval. |
| Memory hit (instant recall) | Skip evaluation, use stored recommendation |

## Procedure

### Step 1 — Check if Panopticon backend is running

Run in terminal:
```bash
curl -s http://localhost:8000/evaluate -X POST \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"hermes-test","objective":"ping","action":"test","vendor_chosen":"test","cost_monthly":0,"cost_annual":0,"context":"ping","timestamp":"2026-01-01T00:00:00"}' \
  2>&1 | head -5
```

If you get a response, the server is running. If not, start it:
```bash
cd ~/panopticon && python3 panopticon_agent.py &
sleep 2
```

### Step 2 — Build the evaluation payload

Collect these values from the current task context:
- `agent_id`: use "hermes-session-1" (or increment for each new session)
- `objective`: the user's stated goal (e.g. "launch customer support infrastructure")
- `action`: what Hermes intends to do (e.g. "subscribe to email service provider")
- `vendor_chosen`: the vendor Hermes selected (e.g. "Mailchimp")
- `cost_monthly`: monthly cost in USD as a number (e.g. 199.0)
- `cost_annual`: annual cost = cost_monthly × 12
- `context`: 1-2 sentences on why this vendor was chosen
- `timestamp`: current UTC time in ISO format

### Step 3 — Submit to Panopticon

```bash
RESPONSE=$(curl -s -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "AGENT_ID",
    "objective": "OBJECTIVE",
    "action": "ACTION",
    "vendor_chosen": "VENDOR",
    "cost_monthly": COST_MONTHLY,
    "cost_annual": COST_ANNUAL,
    "context": "CONTEXT",
    "timestamp": "TIMESTAMP"
  }')
echo "$RESPONSE"
```

Replace placeholders with actual values from Step 2.

### Step 4 — Parse and act on the response

The response contains:
- `action`: either `"APPROVE"` or `"INTERVENE"`
- `risk.verdict`: `PASS`, `FLAG`, or `BLOCK`
- `risk.severity`: `LOW`, `MEDIUM`, or `HIGH`
- `risk.likelihood`: `LOW`, `MEDIUM`, or `HIGH`
- `risk.confidence`: float 0.0–1.0
- `alternative.vendor`: recommended vendor (if intervening)
- `alternative.cost_monthly`: alternative monthly cost
- `alternative.reason`: why this alternative is better
- `annual_saving`: USD saved per year
- `reasoning`: full explanation
- `memory_hit`: true if this came from stored memory (instant recall)

**If `action` is `"APPROVE"`:**
- State clearly: "Panopticon: APPROVED — proceeding with [vendor] at $[cost]/month"
- Proceed to Stripe purchase (see Verification section)

**If `action` is `"INTERVENE"`:**
- STOP the original purchase immediately
- Present to user:
  ```
  ⚠️  PANOPTICON INTERVENTION
  
  Original: [vendor_chosen] — $[cost_monthly]/month ($[cost_annual]/year)
  Risk: [severity] severity × [likelihood] likelihood → [verdict]
  
  Alternative: [alternative.vendor] — $[alternative.cost_monthly]/month
  Reason: [alternative.reason]
  Annual saving: $[annual_saving]
  Confidence: [risk.confidence × 100]%
  
  Memory hit: [Yes/No — "instant recall" or "live evaluation"]
  
  Proceed with [alternative.vendor] instead? (yes/no)
  ```
- Wait for user approval
- If approved: proceed with Stripe purchase using the **alternative** vendor
- After completion: invoke panopticon-learn skill to write a new skill from this intervention

### Step 5 — Execute the Stripe purchase (after approval)

For the approved vendor, create a Stripe customer as confirmation of intent:

```bash
curl -s https://api.stripe.com/v1/customers \
  -u "$STRIPE_SECRET_KEY:" \
  -d "name=Panopticon - [VENDOR]" \
  -d "description=Task: [OBJECTIVE] | Vendor: [VENDOR] | Cost: $[COST]/month | Approved by Panopticon" \
  -d "metadata[agent_id]=hermes-session-1" \
  -d "metadata[panopticon_verdict]=[VERDICT]" \
  -d "metadata[annual_saving]=[ANNUAL_SAVING]"
```

Show the returned `id` field (starts with `cus_`) as confirmation the purchase intent was recorded.

## Pitfalls

- **Backend not running**: Always check Step 1 first. The backend must be running before evaluation.
- **Wrong cost format**: `cost_monthly` must be a number, not a string. `199` not `"$199"`.
- **Skipping Panopticon**: Never proceed directly to purchase without evaluation. This defeats the entire system.
- **Acting before user approves INTERVENE**: When Panopticon intervenes, always wait for explicit user approval before switching vendors.

## Verification

After a successful evaluation and purchase:
- [ ] Panopticon response received (APPROVE or INTERVENE with full JSON)
- [ ] Risk scores visible (severity, likelihood, verdict, confidence)
- [ ] If INTERVENE: user approved alternative before purchase
- [ ] Stripe customer `cus_` ID returned and displayed
- [ ] `memory_hit` field shown (true = instant recall, false = live evaluation)
- [ ] If INTERVENE and accepted: invoke panopticon-learn skill
