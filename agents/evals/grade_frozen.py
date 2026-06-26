
import json
import argparse
from evals.load_golden import load_golden
from core.llm_client import complete

MODEL_OLD  = "deepseek/deepseek-v4-flash"
MODEL_NEW  = "nvidia/nemotron-3-super-120b-a12b:free"

def grade_driver(frozen: list[dict], cases, model: str) -> dict:
    """Grade driver quality on flagged/escalated outputs using the given model."""
    scores = []
    details = []

    for output in frozen:
        if output["action"] not in ("flag", "escalate"):
            continue

        case = next(c for c in cases if c.case_id == output["case_id"])

        messages = [
            {"role": "system", "content": (
                "Score the agent's driver classification.\n"
                "1.0 — correct driver_type AND description clearly explains why\n"
                "0.5 — correct driver_type BUT description is vague or missing detail\n"
                "0.0 — wrong driver_type, or description contradicts the driver.\n"
                "Respond only in JSON: {\"score\": 0|0.5|1, \"reason\": \"one sentence\"}"
            )},
            {"role": "user", "content": (
                f"Expected driver: {case.expected_output.driver_type}\n"
                f"Expected description: {case.expected_output.description}\n"
                f"Agent driver: {output['driver_type']}\n"
                f"Agent description: {output['description']}"
            )}
        ]

        try:
            response = complete(messages, model=model)
            response = complete(messages, model=model)
            if output["case_id"] in ("fpa_020", "fpa_021"):
                print(f"  DEBUG {output['case_id']} raw response: {response!r}")
            if not response:
                scores.append(0.0)
                details.append(f"{output['case_id']}: judge returned empty/None — skipped")
                continue
            clean = (response.strip()
                     .removeprefix("```json").removeprefix("```")
                     .removesuffix("```").strip())
            if not clean:
                scores.append(0.0)
                details.append(f"{output['case_id']}: judge returned blank after strip")
                continue
            result = json.loads(clean)
            scores.append(result["score"])
            details.append(f"{output['case_id']}: {result['reason']}")
        except json.JSONDecodeError:
            scores.append(0.0)
            details.append(f"{output['case_id']}: judge returned non-JSON: {response[:80]!r}")
        except Exception as e:
            scores.append(0.0)
            details.append(f"{output['case_id']}: judge error — {e}")
    return {
        "model": model,
        "cases_judged": len(scores),
        "mean_score": sum(scores) / len(scores) if scores else 0.0,
        "details": details
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--frozen", default="evals/frozen_outputs.json")
    parser.add_argument("--golden", default="data/golden.jsonl")
    args = parser.parse_args()

    with open(args.frozen) as f:
        frozen = json.load(f)

    cases = load_golden(args.golden)

    print("Grading with OLD judge (DeepSeek)...")
    old = grade_driver(frozen, cases, MODEL_OLD)

    print("Grading with NEW judge (Nemotron)...")
    new = grade_driver(frozen, cases, MODEL_NEW)

    print(f"\n{'='*50}")
    print(f"{'Judge':<35} {'Cases':>6} {'Mean':>6}")
    print(f"{'-'*50}")
    print(f"{old['model']:<35} {old['cases_judged']:>6} {old['mean_score']:>6.3f}")
    print(f"{new['model']:<35} {new['cases_judged']:>6} {new['mean_score']:>6.3f}")
    print(f"\nGrader effect (new - old): {new['mean_score'] - old['mean_score']:+.3f}")
    print(f"{'='*50}")

    print("\n--- Old judge details ---")
    for d in old["details"]:
        print(f"  {d}")

    print("\n--- New judge details ---")
    for d in new["details"]:
        print(f"  {d}")


if __name__ == "__main__":
    main()