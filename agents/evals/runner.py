from evals.schemas import GoldenCase, AgentOutput
from evals.load_golden import load_golden
from sklearn.metrics import precision_recall_fscore_support
from core.llm_client import complete
from domain_fpa.agent import run_fpa_agent
import json

def run_case(case: GoldenCase, agent_fn) -> AgentOutput:
    # calls agent_fn with case.input, injects case_id, returns AgentOutput
    result = agent_fn(case.case_id, case.input)
    return result

def score_detection(cases: list[GoldenCase], outputs: list[AgentOutput]) -> dict:
    # computes precision / recall / F1
    ACTIONS = {
        "flag": 1,
        "escalate": 1,
        "do_nothing": 0
    }
    y_true = []
    y_pred = []
    for output in outputs:
        case = next(c for c in cases if c.case_id == output.case_id)
        y_true.append(ACTIONS[case.expected_output.action])
        y_pred.append(ACTIONS[output.action])
    
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="binary", zero_division=0
    )
    return {"precision": precision, "recall": recall, "f1": f1}

def score_driver(cases: list[GoldenCase], outputs: list[AgentOutput]) -> dict:
    # LLM-as-judge for flagged cases only
    cases_judged = 0
    score =[]
    details =[]
    output_list = []
    for output in outputs:
        action = output.action
        if action == "escalate" or action == "flag":
            output_list.append(output)
    
    for output in output_list:
    # find matching golden case
        case = next(c for c in cases if c.case_id == output.case_id)
        
        messages = [
            {"role": "system", "content": """1.0 — correct driver_type AND description clearly explains why
            0.5 — correct driver_type BUT description is vague or missing detail  
            0.0 — wrong driver_type, or description contradicts the driver.
            Respond only in JSON: {"score": 0|0.5|1, "reason": "one sentence"}"""},
            {"role": "user", "content": f"""
            Expected driver: {case.expected_output.driver_type}
            Expected description: {case.expected_output.description}
            Agent driver: {output.driver_type}
            Agent description: {output.description}
            """}
        ]
        
        response = complete(messages)
        clean = response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        if not clean:
            score.append(0.0)
            details.append("LLM judge returned empty response")
            cases_judged += 1
            continue
        result = json.loads(clean)
        cases_judged += 1
        score.append(result["score"])
        details.append(result["reason"])
    
    return {
        "cases_judged": cases_judged,
        "mean_score": sum(score) / len(score) if score else 0.0,
        "details": details
    }

 
def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=str, default=None,
        help="Comma-separated case IDs to run, e.g. --cases fpa_014,fpa_015,fpa_016")
    parser.add_argument("--limit", type=int, default=None,
        help="Run only the first N cases")
    args = parser.parse_args()

    cases = load_golden("data/golden.jsonl")

    if args.cases:
        ids = set(args.cases.split(","))
        cases = [c for c in cases if c.case_id in ids]
    elif args.limit:
        cases = cases[:args.limit]

    outputs = []
    for case in cases:
        print(f"Running {case.case_id}...")
        try:
            result = run_case(case, run_fpa_agent)
            outputs.append(result)
            print(f"  OK: {result.action}")
        except Exception as e:
            print(f"  FAILED: {e}")

    detection = score_detection(cases, outputs)
    driver = score_driver(cases, outputs)

    print("=== Detection Scores ===")
    print(f"Precision: {detection['precision']:.2f}")
    print(f"Recall:    {detection['recall']:.2f}")
    print(f"F1:        {detection['f1']:.2f}")

    print("\n=== Driver Scores ===")
    print(f"Cases judged: {driver['cases_judged']}")
    print(f"Mean score:   {driver['mean_score']:.2f}")
    print(f"Details: {driver['details']}")
    for d in driver['details']:
        print(f"  - {d}")

if __name__ == "__main__":
    main()