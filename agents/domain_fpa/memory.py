import json
from core.memory import store

def case_to_text(case: dict) -> str:
    return (
        f"case_id={case['case_id']} "
        f"account_id={case['input']['account_id']} "
        f"period={case['input']['period']} "
        f"driver={case['expected_output']['driver_type']} "
        f"description={case['expected_output']['description']}"
    )

def load_and_store(jsonl_path: str):
    with open(jsonl_path) as f:
        for line in f:
            case = json.loads(line)
            text = case_to_text(case)
            store(
                case_text=text,
                case_id=case["case_id"],
                account_id=case["input"]["account_id"],
                period=case["input"]["period"],
                confirmed_driver=case["expected_output"]["driver_type"],
                confirmed_action=case["expected_output"]["action"],
                description=case["expected_output"]["description"]

            )
            print(f"stored {case['case_id']}")

if __name__ == "__main__":
    load_and_store("data/static_cases.jsonl")