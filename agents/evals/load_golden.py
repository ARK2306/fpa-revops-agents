import json
from pathlib import Path
from evals.schemas import GoldenCase

def load_golden(path: Path) -> list[GoldenCase]:
    cases = []
    with open(path) as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
                cases.append(GoldenCase(**raw))
            except Exception as e:
                raise ValueError(f"Case {i+1} failed validation: {e}")
    return cases

if __name__ == "__main__":
    path = Path("data/golden.jsonl")
    cases = load_golden(path)
    print(f"Loaded {len(cases)} cases")
    for c in cases:
        print(f"  {c.case_id} | {c.case_type} | {c.expected_output.action}")