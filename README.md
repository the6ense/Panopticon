# Panopticon

**Collective intelligence oversight for autonomous agent ecosystems.**

Panopticon is a Hermes Agent skill bundle that sits above your agent's decision-making, evaluates every vendor choice before money moves, and gets smarter after every intervention — writing new skills from its own experience.

Built for the [Hermes Agent Accelerated Business Hackathon](https://hermes-agent.nousresearch.com) by NVIDIA, Stripe & Nous Research.

---

## The Problem

AI agents operating autonomously make purchasing decisions in isolation. Agent A overpays for email hosting. Agent B does the same thing next week. No knowledge transfer. Compounding waste.

## What Panopticon Does

Before any purchase, Panopticon:

1. **Checks memory** — has it seen this vendor category before? If yes, instant recommendation (0.00s)
2. **Evaluates live** — if not, calls Nemotron to score risk (severity × likelihood) and find alternatives
3. **Intervenes when needed** — blocks bad purchases, presents better options
4. **Learns permanently** — writes a new Hermes skill from every accepted intervention

The result: every agent in your ecosystem benefits from every other agent's experience.

## Demo

| Scenario | Time | What happens |
|---|---|---|
| Scenario 1 | ~15s | Live evaluation: Worker picks $199/mo email provider → Panopticon intervenes → $29/mo alternative → $2,040/yr saved |
| Scenario 2 | 0.00s | New agent, same category → Panopticon recalls instantly from prior skill → no evaluation needed |

## Install

```bash
# Install Panopticon skills
hermes skills tap add github:yourusername/panopticon

# Copy the bundle
cp skill-bundles/panopticon.yaml ~/.hermes/skill-bundles/

# Start the evaluation backend
cd backend && pip install -r requirements.txt
python3 panopticon_agent.py &

# Add your API keys to ~/.hermes/.env
echo "NVIDIA_API_KEY=your-key" >> ~/.hermes/.env
echo "STRIPE_SECRET_KEY=sk_test_your-key" >> ~/.hermes/.env
```

Then in Hermes:
```
/panopticon
Your task: launch customer support infrastructure, set up email
```

## Repository Structure

```
panopticon/
├── skills/
│   └── panopticon/
│       ├── evaluate/SKILL.md    ← risk scoring + vendor evaluation
│       ├── remember/SKILL.md    ← memory read/write
│       └── learn/SKILL.md       ← self-improvement loop
├── skill-bundles/
│   └── panopticon.yaml          ← /panopticon slash command
├── backend/
│   ├── panopticon_agent.py      ← HTTP evaluation server (Nemotron)
│   ├── memory.py                ← SQLite memory store
│   └── schema.py                ← data classes
└── README.md
```

## Technical Stack

| Layer | Tool |
|---|---|
| Agent runtime | Hermes Agent |
| Evaluation backend | NVIDIA Nemotron 3 Super 120B |
| Memory | SQLite |
| Financial transactions | Stripe (test mode) |
| Policy enforcement | NVIDIA NemoClaw |
| Self-improvement | Hermes `skill_manage` + `/learn` |

## The Long-Term Vision

At scale, Panopticon accumulates vendor intelligence across thousands of agents and millions of decisions. This becomes:

- **Instant recall** for any vendor category — no evaluation cost
- **Panopticon Verified** — a trust benchmark for the agent economy (like a credit score for vendors serving autonomous buyers)
- **Commission model** — Panopticon earns a small cut when its intervention leads to a better purchase

---

Built with [Hermes Agent](https://hermes-agent.nousresearch.com) · MIT License
