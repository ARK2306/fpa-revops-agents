# agents/evals/freeze_outputs.py
import json
from evals.load_golden import load_golden
from domain_fpa.agent import run_fpa_agent

def main():
    cases = load_golden("data/golden.jsonl")
    frozen = []
    
    for case in cases:
        print(f"Running {case.case_id}...")
        try:
            output, usage = run_fpa_agent(case.case_id, case.input)
            frozen.append({
                "case_id": output.case_id,
                "action": output.action,
                "driver_type": output.driver_type,
                "magnitude": output.magnitude,
                "confidence": output.confidence,
                "description": output.description,
                "grounding": {
                    "transaction_ids": output.grounding.transaction_ids,
                    "signal": output.grounding.signal
                }
            })
            print(f"  OK: {output.action} / {output.driver_type}")
        except Exception as e:
            print(f"  FAILED: {e}")
    
    with open("evals/frozen_outputs.json", "w") as f:
        json.dump(frozen, f, indent=2)
    
    print(f"\nFrozen {len(frozen)} outputs → evals/frozen_outputs.json")

if __name__ == "__main__":
    main()