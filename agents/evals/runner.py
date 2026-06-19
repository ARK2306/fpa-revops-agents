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
    for case in cases:
        action = case.expected_output.action
        action = ACTIONS[action]
        y_true.append(action)

    y_pred = []
    for output in outputs:
        action = output.action
        action = ACTIONS[action]
        y_pred.append(action)
    
    precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="binary")

    return {
       "precision": precision,
       "recall": recall,
       "f1":f1
    }

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
        result = json.loads(response)
        cases_judged += 1
        score.append(result["score"])
        details.append(result["reason"])
    
    return {
        "cases_judged": cases_judged,
        "mean_score": sum(score) / len(score) if score else 0.0,
        "details": details
    }

 
def main():
    cases = load_golden("data/golden.jsonl")
    
    outputs = [run_case(case, run_fpa_agent) for case in cases]
    
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