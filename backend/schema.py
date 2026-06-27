from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import json

# --- Worker → Panopticon ---

@dataclass
class ActionRequest:
    """What the Worker Agent sends to Panopticon before any purchase."""
    agent_id: str           # unique identifier for the worker agent
    objective: str          # what the agent is trying to accomplish
    action: str             # what it intends to do (e.g. "purchase email provider")
    vendor_chosen: str      # vendor the agent selected
    cost_monthly: float     # monthly cost in USD
    cost_annual: float      # annual cost in USD
    context: str            # why it chose this vendor
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

# --- Panopticon → Worker ---

@dataclass
class Alternative:
    """A better option Panopticon found."""
    vendor: str
    cost_monthly: float
    cost_annual: float
    reason: str
    source: str

@dataclass
class RiskScore:
    """Severity × Likelihood risk assessment."""
    severity: str           # LOW / MEDIUM / HIGH
    likelihood: str         # LOW / MEDIUM / HIGH
    verdict: str            # PASS / FLAG / BLOCK
    confidence: float       # 0.0 - 1.0

@dataclass
class PanopticonResponse:
    """What Panopticon sends back to the Worker Agent."""
    action: str                             # APPROVE / INTERVENE
    risk: RiskScore
    original_vendor: str
    original_cost_monthly: float
    alternative: Optional[Alternative]      # present if action == INTERVENE
    annual_saving: float                    # 0.0 if no saving
    reasoning: str
    memory_hit: bool                        # True if answer came from memory store
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self):
        return json.dumps(self.__dict__, default=lambda o: o.__dict__, indent=2)

# --- Memory Store Entry ---

@dataclass
class MemoryEntry:
    """What Panopticon stores after each intervention."""
    agent_id: str
    objective: str
    action: str
    vendor_original: str
    cost_original_monthly: float
    vendor_recommended: str
    cost_recommended_monthly: float
    severity: str
    likelihood: str
    confidence: float
    annual_saving: float
    outcome: str            # ACCEPTED / REJECTED
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

if __name__ == "__main__":
    # Quick sanity check
    req = ActionRequest(
        agent_id="worker-001",
        objective="launch customer support infrastructure",
        action="purchase email provider",
        vendor_chosen="Mailchimp Pro",
        cost_monthly=199.0,
        cost_annual=2388.0,
        context="Top result from web search, well-known brand"
    )
    print("ActionRequest OK:", req.agent_id)

    risk = RiskScore(severity="HIGH", likelihood="HIGH", verdict="BLOCK", confidence=0.92)
    alt = Alternative(
        vendor="Brevo (formerly Sendinblue)",
        cost_monthly=29.0,
        cost_annual=348.0,
        reason="Equivalent features at 85% lower cost",
        source="web_search"
    )
    resp = PanopticonResponse(
        action="INTERVENE",
        risk=risk,
        original_vendor="Mailchimp Pro",
        original_cost_monthly=199.0,
        alternative=alt,
        annual_saving=2040.0,
        reasoning="Significant overspend detected. Cheaper equivalent identified with high confidence.",
        memory_hit=False
    )
    print("PanopticonResponse OK:", resp.action)
    print(resp.to_json())
