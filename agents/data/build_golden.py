import json
import pandas as pd
from pathlib import Path

MATERIALITY_ABS = 25_000
MATERIALITY_PCT = 0.15
N_TRANSACTIONS = 6  # how many transactions to sample per case

MONTHLY_BUDGET = {
    "4000": 150_000,
    "4100":  40_000,
    "5000": -30_000,
    "5100":  -8_000,
    "6000": -80_000,
    "6100": -25_000,
    "6200": -10_000,
}

def load_data():
    csv_path = "data/transactions.csv"
    json_path = "data/answer_key.json"
    transactions = pd.read_csv(csv_path)
    transactions["account_id"] = transactions["account_id"].astype(str)
    with open(json_path) as f:
        ans_key = json.load(f)

    return transactions, ans_key

def compute_variance(transactions, budget):
    actual = sum(t["amount"] for t in transactions)
    variance = actual - budget
    variance_pct = variance / abs(budget)
    return variance, variance_pct

def build_case_from_driver(case_id, driver, transactions_df, n=6):
    account_id = driver["account_id"]
    period = driver["period"]
    budget = MONTHLY_BUDGET[account_id]
    
    tx = transactions_df[
        (transactions_df["account_id"] == account_id) &
        (transactions_df["period"] == period)
    ].head(n)
    
    transactions = tx.to_dict(orient="records")
    
    CASE_TYPE_MAP = {
        "price_change":   "easy",
        "one_time_item":  "easy",
        "volume_change":  "easy",
        "timing_accrual": "ambiguous",
        "data_error":     "adversarial",
    }
    
    ACTION_MAP = {
        "price_change":   "flag",
        "one_time_item":  "flag",
        "volume_change":  "flag",
        "timing_accrual": "escalate",
        "data_error":     "do_nothing",
    }

    return dict(
        case_id=case_id,
        case_type=CASE_TYPE_MAP[driver["driver_type"]],
        input=dict(
            period=period,
            account_id=account_id,
            budget=float(budget),
            transactions=transactions
        ),
        expected_output=dict(
            action=ACTION_MAP[driver["driver_type"]],
            driver_type=driver["driver_type"],
            magnitude=driver["magnitude"],
            description=driver["description"],
            grounding=dict(
                transaction_ids=[t["transaction_id"] for t in transactions],
                signal=driver["description"]
            )
        )
    )

def build_do_nothing_case(case_id, period, account_id, budget, transactions_df):
    transactions=transactions_df.to_dict(orient="records")
    variance, variance_pct = compute_variance(transactions=transactions, budget=budget)
    case = dict(case_id=case_id,case_type="easy",input=dict(period=period,account_id=account_id,budget=budget,transactions=transactions), 
                expected_output=dict(action="do_nothing",driver_type="none",magnitude=variance,description="No material variance detected",grounding=dict(transaction_ids=[t["transaction_id"]for t in transactions],signal="No anomalies found") ))
    return case

def main():
    transactions_df, answer_key = load_data()
    cases = []
    case_id_counter = 4
    DO_NOTHING_PERIODS = [
    ("2025-02", "4000", 150_000),
    ("2025-07", "6100", -25_000),
]

    for driver in answer_key:
        case = build_case_from_driver(f"fpa_{case_id_counter:03d}", driver, transactions_df)
        cases.append(case)
        case_id_counter += 1
    

    for period, account_id, budget in DO_NOTHING_PERIODS:
        tx = transactions_df[
            (transactions_df["account_id"] == account_id) &
            (transactions_df["period"] == period)
        ].head(N_TRANSACTIONS)
        case = build_do_nothing_case(f"fpa_{case_id_counter:03d}", period, account_id, budget, tx)
        cases.append(case)
        case_id_counter += 1

    with open("data/golden.jsonl", "a") as f:
        for case in cases:
            f.write(json.dumps(case) + "\n")

if __name__ == "__main__":
    main()