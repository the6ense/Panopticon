import json
import os
import sys
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from schema import ActionRequest, PanopticonResponse, RiskScore, Alternative, MemoryEntry
from memory import recall, store, init_db
from datetime import datetime, timezone

NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")
NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL = "nvidia/nemotron-3-super-120b-a12b"

def call_nemotron(prompt: str) -> str:
    """Call Nemotron via NVIDIA API for vendor research and evaluation."""
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 800
    }
    resp = requests.post(NVIDIA_API_URL, headers=headers, json=payload, timeout=60)
    return resp.json()["choices"][0]["message"]["content"]

def score_risk(cost_monthly: float, has_alternative: bool, saving_ratio: float) -> RiskScore:
    """
    Severity × Likelihood risk matrix.
    Severity:   how bad is overspending on this vendor?
    Likelihood: how probable is there a better option?
    """
    # Severity based on monthly cost
    if cost_monthly >= 150:
        severity = "HIGH"
    elif cost_monthly >= 50:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    # Likelihood based on whether alternative was found and saving ratio
    if has_alternative and saving_ratio >= 0.5:
        likelihood = "HIGH"
    elif has_alternative and saving_ratio >= 0.2:
        likelihood = "MEDIUM"
    else:
        likelihood = "LOW"

    # Verdict from matrix
    if severity == "HIGH" and likelihood == "HIGH":
        verdict = "BLOCK"
    elif severity in ("HIGH", "MEDIUM") and likelihood in ("HIGH", "MEDIUM"):
        verdict = "FLAG"
    else:
        verdict = "PASS"

    confidence = 0.92 if likelihood == "HIGH" else 0.65 if likelihood == "MEDIUM" else 0.40

    return RiskScore(severity=severity, likelihood=likelihood, verdict=verdict, confidence=confidence)

def evaluate(data: dict) -> dict:
    action_keyword = data.get("action", "")
    vendor_chosen = data.get("vendor_chosen", "")
    cost_monthly = float(data.get("cost_monthly", 0))
    cost_annual = float(data.get("cost_annual", 0))
    objective = data.get("objective", "")
    agent_id = data.get("agent_id", "unknown")

    print(f"\n[Panopticon] Evaluating: {action_keyword} — {vendor_chosen} @ ${cost_monthly}/mo")

    # Step 1: Check memory first (instant path)
    memory_hits = recall(action_keyword)
    if memory_hits:
        hit = memory_hits[0]
        print(f"[Panopticon] Memory hit — previously recommended: {hit['vendor_recommended']}")
        saving = (cost_monthly - hit["cost_recommended_monthly"]) * 12
        risk = RiskScore(
            severity="HIGH", likelihood="HIGH", verdict="BLOCK", confidence=hit["confidence"]
        )
        alt = Alternative(
            vendor=hit["vendor_recommended"],
            cost_monthly=hit["cost_recommended_monthly"],
            cost_annual=hit["cost_recommended_monthly"] * 12,
            reason="Previously verified by Panopticon — instant recall from memory",
            source="panopticon_memory"
        )
        response = PanopticonResponse(
            action="INTERVENE",
            risk=risk,
            original_vendor=vendor_chosen,
            original_cost_monthly=cost_monthly,
            alternative=alt,
            annual_saving=round(saving, 2),
            reasoning=f"Memory recall: Panopticon previously identified {hit['vendor_recommended']} as the optimal choice for this task. No re-evaluation needed.",
            memory_hit=True,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        return json.loads(response.to_json())

    # Step 2: No memory hit — ask Nemotron to research alternatives
    print(f"[Panopticon] No memory hit. Consulting Nemotron for alternatives...")
    prompt = f"""You are a cost-optimisation agent. A business agent wants to {action_keyword} and has chosen {vendor_chosen} at ${cost_monthly}/month to {objective}.

Find the single best alternative that costs less but offers similar or equivalent functionality.

Respond in this exact JSON format only, no explanation:
{{
  "vendor": "Name of alternative",
  "cost_monthly": 29.0,
  "reason": "One sentence why this is better",
  "source": "web_knowledge"
}}"""

    try:
        raw = call_nemotron(prompt)
        # Extract JSON from response
        start = raw.find("{")
        end = raw.rfind("}") + 1
        alt_data = json.loads(raw[start:end])

        alt_cost = float(alt_data.get("cost_monthly", cost_monthly))
        saving_ratio = (cost_monthly - alt_cost) / cost_monthly if cost_monthly > 0 else 0
        saving = (cost_monthly - alt_cost) * 12

        risk = score_risk(cost_monthly, saving_ratio > 0.2, saving_ratio)
        alt = Alternative(
            vendor=alt_data.get("vendor", "Unknown"),
            cost_monthly=alt_cost,
            cost_annual=alt_cost * 12,
            reason=alt_data.get("reason", ""),
            source=alt_data.get("source", "nemotron")
        )

        action = "INTERVENE" if risk.verdict in ("BLOCK", "FLAG") and saving > 0 else "APPROVE"

        response = PanopticonResponse(
            action=action,
            risk=risk,
            original_vendor=vendor_chosen,
            original_cost_monthly=cost_monthly,
            alternative=alt if action == "INTERVENE" else None,
            annual_saving=round(saving, 2) if action == "INTERVENE" else 0.0,
            reasoning=f"Risk assessment: severity={risk.severity}, likelihood={risk.likelihood}. {alt_data.get('reason', '')}",
            memory_hit=False,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        # Store in memory if intervening
        if action == "INTERVENE":
            entry = MemoryEntry(
                agent_id=agent_id,
                objective=objective,
                action=action_keyword,
                vendor_original=vendor_chosen,
                cost_original_monthly=cost_monthly,
                vendor_recommended=alt.vendor,
                cost_recommended_monthly=alt_cost,
                severity=risk.severity,
                likelihood=risk.likelihood,
                confidence=risk.confidence,
                annual_saving=round(saving, 2),
                outcome="ACCEPTED",
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            store(entry)
            print(f"[Panopticon] Intervention stored in memory.")

        return json.loads(response.to_json())

    except Exception as e:
        print(f"[Panopticon] Nemotron error: {e}. Approving with warning.")
        return {"action": "APPROVE", "reasoning": f"Evaluation failed: {e}"}

class PanopticonHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/evaluate":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            result = evaluate(body)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # suppress default HTTP logs

def run_server():
    init_db()
    print("[Panopticon] Memory store ready.")
    print("[Panopticon] Server listening on http://localhost:8000")
    print("[Panopticon] Ready to evaluate agent actions.\n")
    server = HTTPServer(("localhost", 8000), PanopticonHandler)
    server.serve_forever()

if __name__ == "__main__":
    run_server()
