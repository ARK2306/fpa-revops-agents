import pandas as pd
import numpy as np
import json
import random
from pathlib import Path

# ── Constants ──────────────────────────────────────────────────────────────────
SEED = 42                  # makes every run reproducible — same random numbers every time
MATERIALITY_ABS = 25_000   # flag a variance if it's over $25k in absolute dollars...
MATERIALITY_PCT = 0.15     # ...OR over 15% of budget (whichever trips first)

random.seed(SEED)
np.random.seed(SEED)

# ── Chart of accounts ──────────────────────────────────────────────────────────
# account_type tells us whether a variance is favorable or unfavorable later.
# "Income" over budget = good. "Expense" over budget = bad. Same math, opposite meaning.

ACCOUNTS = pd.DataFrame([
    {"account_id": "4000", "account_name": "Software Revenue",      "account_type": "Income"},
    {"account_id": "4100", "account_name": "Services Revenue",      "account_type": "Income"},
    {"account_id": "5000", "account_name": "Hosting & Infra",       "account_type": "Cost of Goods Sold"},
    {"account_id": "5100", "account_name": "Third-Party APIs",      "account_type": "Cost of Goods Sold"},
    {"account_id": "6000", "account_name": "Salaries & Benefits",   "account_type": "Expense"},
    {"account_id": "6100", "account_name": "Sales & Marketing",     "account_type": "Expense"},
    {"account_id": "6200", "account_name": "General & Admin",       "account_type": "Expense"},
])

# ── Periods ────────────────────────────────────────────────────────────────────
# 12 months of 2025. Every budget row and transaction will reference one of these.

PERIODS = [f"2025-{m:02d}" for m in range(1, 13)]

MONTHLY_BUDGET = {
    "4000": 150_000,   # Software Revenue
    "4100":  40_000,   # Services Revenue
    "5000": -30_000,   # Hosting & Infra  (negative = cost)
    "5100":  -8_000,   # Third-Party APIs
    "6000": -80_000,   # Salaries
    "6100": -25_000,   # Sales & Marketing
    "6200": -10_000,   # G&A
}


def build_budget():
    cartesian_product = pd.MultiIndex.from_product([ACCOUNTS["account_id"],PERIODS],names=["account_id","period"]).to_frame(index=False)
    cartesian_product["budget"] = cartesian_product["account_id"].map(MONTHLY_BUDGET)
    return cartesian_product

def build_baseline_transactions():
    budget_df = build_budget()
    all_rows = []
    tx_counter = 1
    DESCRIPTIONS = {
    "4000": ["Monthly SaaS subscription", "Annual license renewal", "Software seat expansion"],
    "4100": ["Professional services invoice", "Implementation fee", "Consulting engagement"],
    "5000": ["AWS invoice", "Cloudflare charge", "GCP compute bill"],
    "5100": ["Stripe API fees", "Twilio usage charge", "SendGrid invoice"],
    "6000": ["Payroll", "Benefits administration", "Contractor payment"],
    "6100": ["Google Ads", "Sponsored content", "Trade show expense"],
    "6200": ["Office supplies", "Legal fees", "Accounting services"],
}
    for _, row in budget_df.iterrows():
        account_id = row["account_id"]
        period = row["period"]
        budget_amount = row["budget"]

        n = random.randint(6, 12)
        noise = np.random.uniform(-0.05, 0.05)
        total = budget_amount * (1 + noise)
        weights = np.random.dirichlet(np.ones(n)*3)
        amounts = weights * total
        year, month = int(period.split("-")[0]), int(period.split("-")[1])
        for amt in amounts:
            day = random.randint(1, 28)  # 28 is safe for all months
            row_dict = {
                "transaction_id": f"T{tx_counter:06d}",
                "date": f"{year}-{month:02d}-{day:02d}",
                "account_id": account_id,
                "period": period,
                "amount": float(amt),
                "description": random.choice(DESCRIPTIONS[account_id])
            }
            tx_counter += 1
            all_rows.append(row_dict)
    return pd.DataFrame(all_rows)

def inject_drivers(transactions_df):
    VOLUME_SPIKE_FRAC = 0.5
    df = transactions_df.copy()
    answer_key = []
    price_driver = df.loc[(df["account_id"] == "4000") & (df["period"] == "2025-03")]
    df_pd = 1.35 * price_driver["amount"]
    df.loc[(df["account_id"] == "4000") & (df["period"] == "2025-03"), "amount"] = df_pd
    magnitude = df_pd.sum() - price_driver["amount"].sum()
    answer_key.append({
    "account_id":  "4000",
    "period":      "2025-03",
    "driver_type": "price_change",
    "magnitude":   float(magnitude),
    "description": "All Software Revenue lines ~35% above budget"
})
    one_time_row = pd.DataFrame([{
    "transaction_id": "T999001",
    "date":           "2025-06-15",
    "account_id":     "6100",
    "period":         "2025-06",
    "amount":         -40_000.0,
    "description":    "Legal settlement - one time"
}])
    df = pd.concat([df, one_time_row], ignore_index=True)
    answer_key.append({
        "account_id":  "6100",
        "period":      "2025-06",
        "driver_type": "one_time_item",
        "magnitude":   -40_000.0,
        "description": "Single legal settlement posted to Sales & Marketing"
    })

    vc = df.loc[(df["account_id"] == "4100") & (df["period"] == "2025-09")]
    vc_sample = vc.sample(frac=VOLUME_SPIKE_FRAC)
    df = pd.concat([df, vc_sample], ignore_index=True)
    duplicates = df.duplicated(subset='transaction_id')
    n_dupes = duplicates.sum()
    new_ids = [f"T{999100 + i:06d}" for i in range(n_dupes)]
    df.loc[duplicates, "transaction_id"] = new_ids
    mag = vc_sample["amount"].sum()
    answer_key.append({
    "account_id":  "4100",
    "period":      "2025-09",
    "driver_type": "volume_change",
    "magnitude":   float(mag),
    "description": "Volume spike — ~50% more invoices than normal in Services Revenue"
})
    ta = df.loc[(df["account_id"] == "5000") & (df["period"] == "2025-10")]
    ta_sample = ta.sample(n=5)
    df.loc[ta_sample.index, 'period'] = "2025-11"
    magnitude = float(df.loc[ta_sample.index, "amount"].sum())
    answer_key.append({
    "account_id":  "5000",
    "period":      "2025-11",
    "driver_type": "timing_accrual",
    "magnitude":   magnitude,
    "description": "5 Hosting & Infra transactions dated in October posted to November period — date/period mismatch is the signal"
    })
    de = df.loc[(df["account_id"] == "4100") & (df["period"] == "2025-08")]
    de_sample = de.sample(n=3)
    df.loc[de_sample.index, "account_id"] = "4000"
    magnitude = float(df.loc[de_sample.index, "amount"].sum())
    answer_key.append({
        "account_id":  "4000",
        "period":      "2025-08",
        "driver_type": "data_error",
        "magnitude":   magnitude,
        "description": "3 Services Revenue transactions miscoded to Software Revenue — description mismatch is the signal"
    })

    return df, answer_key

def save_outputs(budget_df, transactions_df, answer_key):
    out = Path(__file__).parent
    
    budget_df.to_csv(out / "budget.csv", index=False)
    transactions_df.to_csv(out / "transactions.csv", index=False)
    
    with open(out / "answer_key.json", "w") as f:
        json.dump(answer_key, f, indent=2)
    
    print(f"Saved budget.csv ({len(budget_df)} rows)")
    print(f"Saved transactions.csv ({len(transactions_df)} rows)")
    print(f"Saved answer_key.json ({len(answer_key)} drivers)")


# ── Sanity check ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    budget      = build_budget()
    baseline    = build_baseline_transactions()
    transactions, answer_key = inject_drivers(baseline)
    save_outputs(budget, transactions, answer_key)
    df = pd.read_csv("data/transactions.csv")
    df["account_id"] = df["account_id"].astype(str)
    actuals = df[df["period"] == "2025-01"].groupby("account_id")["amount"].sum().reset_index()
    jan_budget = budget[budget["period"] == "2025-01"]
    merged = actuals.merge(jan_budget, on="account_id")
    merged["variance"] = merged["amount"] - merged["budget"]
    merged["variance_pct"] = merged["variance"] / merged["budget"].abs()
    print(merged[["account_id", "amount", "budget", "variance", "variance_pct"]].to_string(index=False))

    

    