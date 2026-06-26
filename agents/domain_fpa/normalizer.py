import pandas as pd

REQUIRED_COLUMNS = [
    "transaction_id", "account_id", "period",
    "date", "amount", "description"
]

def normalize_csv(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    missing = set(REQUIRED_COLUMNS) - {"period"} - set(mapping.keys())
    if missing:
        raise ValueError(f"Column mapping incomplete — missing: {missing}")

    rename = {v: k for k, v in mapping.items()}
    df = df.rename(columns=rename)

    # derive period from date if not explicitly mapped
    if "period" not in df.columns:
        if "date" not in df.columns:
            raise ValueError("Cannot derive period — date column not mapped")
        df["period"] = pd.to_datetime(df["date"]).dt.to_period("M").astype(str)
    
    # coerce types
    df["account_id"] = df["account_id"].astype(str)
    df["transaction_id"] = df["transaction_id"].astype(str)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df["period"] = df["period"].astype(str).str[:7]

    return df[REQUIRED_COLUMNS]