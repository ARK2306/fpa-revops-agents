"""
Re-freeze golden inputs for fpa_001, fpa_002, fpa_003, fpa_004 in static_cases.jsonl.
Run from the agents/ directory:  python ../fix_static_cases.py

Only the input.transactions and input.budget fields are updated.
All expected_output fields are left exactly as-is.
"""
import csv, json, sys
from pathlib import Path
from collections import defaultdict

TX_PATH     = Path("data/transactions.csv")
STATIC_PATH = Path("data/static_cases.jsonl")

STALE = {
    "fpa_001": ("4000", "2025-03"),
    "fpa_002": ("6100", "2025-06"),
    "fpa_003": ("4100", "2025-09"),
    "fpa_004": ("5000", "2025-11"),
    "fpa_005": ("4000", "2025-08"),  # add
    "fpa_008": ("4000", "2025-02"),  # add
    "fpa_009": ("6100", "2025-07"),
}

# Load CSV rows and budget
tx = defaultdict(list)
bud = {}
for r in csv.DictReader(TX_PATH.open()):
    tx[(r["account_id"], r["period"])].append(r)

# budget.csv lives alongside transactions.csv
bud_path = TX_PATH.parent / "budget.csv"
for r in csv.DictReader(bud_path.open()):
    bud[(r["account_id"], r["period"])] = float(r["budget"])

# Read, patch, write
lines = [l for l in STATIC_PATH.open() if l.strip()]
patched = []
counts = {}
for line in lines:
    g = json.loads(line)
    cid = g["case_id"]
    if cid in STALE:
        acct, per = STALE[cid]
        csv_rows = tx.get((acct, per), [])
        if not csv_rows:
            print(f"ERROR: no CSV rows found for {cid} ({acct},{per})")
            sys.exit(1)
        new_txs = [
            {
                "transaction_id": r["transaction_id"],
                "date":           r["date"],
                "account_id":     r["account_id"],
                "period":         r["period"],
                "amount":         float(r["amount"]),
                "description":    r["description"],
            }
            for r in csv_rows
        ]
        old_n = len(g["input"]["transactions"])
        g["input"]["transactions"] = new_txs
        g["input"]["budget"]       = bud.get((acct, per), g["input"]["budget"])
        counts[cid] = (old_n, len(new_txs))
    patched.append(json.dumps(g))

with STATIC_PATH.open("w") as f:
    f.write("\n".join(patched) + "\n")

for cid, (old, new) in counts.items():
    print(f"  {cid}: {old} frozen tx -> {new} CSV rows re-frozen")
print("Done — static_cases.jsonl updated. Run build_golden.py to rebuild golden.jsonl.")