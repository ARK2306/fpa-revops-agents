import pandas as pd

TRANSACTIONS_PATH = "data/transactions.csv"
BUDGET_PATH = "data/budget.csv"

def _load_transactions() -> pd.DataFrame:
    df = pd.read_csv(TRANSACTIONS_PATH)
    df["account_id"] = df["account_id"].astype(str)
    return df

def query_actuals(period: str, account_id: str | None = None) -> list[dict]:
    df = _load_transactions()
    res = df[df["period"] == period]
    if account_id:
        res = res[res["account_id"] == account_id]
    res = res.groupby("account_id")["amount"].sum()
    
    key = []

    for account_id_val, amount in res.items():
        key.append({
            "account_id": account_id_val,
            "actual_amount": amount
        })

    return key

QUERY_ACTUALS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "query_actuals",
        "description": "Get the summed actual amounts per account for a given period. Use this first to find which accounts have material variances.",
        "parameters": {
            "type": "object",
            "required": ["period", "account_id"],
            "properties": {
                "period": {
                    "type": "string",
                    "description": "The period to query in YYYY-MM format, e.g. '2025-03'"
                },
                "account_id": {
                    "type": "string",
                    "description": "Optional. Filter to a single account. Omit to get all accounts for the period."
                }
            },
            "required": ["period"]
        }
    }
}

def _load_budget():
    df = pd.read_csv(BUDGET_PATH)
    df["account_id"] = df["account_id"].astype(str)
    return df

def query_budget(period: str, account_id: str | None = None) -> list[dict]:
    df = _load_budget()
    res = df[df["period"]== period]
    if account_id:
        res = res[res["account_id"] == account_id]
    res = res.groupby("account_id")["budget"].sum()
    
    key = []

    for account_id_val, budget in res.items():
        key.append({
            "account_id": account_id_val,
            "budget_amount": budget
        })

    return key

QUERY_BUDGET_SCHEMA = {
    "type": "function",
    "function": {
        "name": "query_budget",
        "description": "Get the budgeted amount per account for a given period. Use alongside query_actuals to compute variances.",
        "parameters": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "description": "The period to query in YYYY-MM format, e.g. '2025-03'"
                },
                "account_id": {
                    "type": "string",
                    "description": "Optional. Filter to a single account. Omit to get all accounts for the period."
                }
            },
            "required": ["period"]
        }
    }
}

def get_transactions(period: str, account_id: str) -> list[dict]:
    df = _load_transactions()
    res = df[(df["period"]== period) & (df["account_id"]==account_id)]
    
    key = res[["transaction_id","date","amount","description"]].to_dict(orient="records")

    return key

GET_TRANSACTIONS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_transactions",
        "description": "Get the individual transaction rows for a specific account and period. Use this after query_actuals identifies a material variance — the transaction rows are your grounding evidence for the driver.",
        "parameters": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "description": "The period in YYYY-MM format, e.g. '2025-03'"
                },
                "account_id": {
                    "type": "string",
                    "description": "The account to retrieve transactions for."
                }
            },
            "required": ["period", "account_id"]
        }
    }
}

def get_prior_periods(account_id: str, current_period: str, n: int = 3) -> list[dict]:

    current = pd.Period(current_period, freq="M")
    prior_periods = [str(current - i) for i in range(1, n + 1)]

    df = _load_transactions()
    res = df[(df["period"].isin(prior_periods)) & (df["account_id"]==account_id)]
    res = res.groupby("period")["amount"].sum()
    key =[]

    for period, amount in res.items():
        key.append(
            {
                "period": period,
                "actual_amount": amount
            }
        )
    
    return key

GET_PRIOR_PERIODS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_prior_periods",
        "description": "Get actual amounts for the same account over the N months before the current period. Use this to distinguish a one-time spike from a trend, or to check if a variance is seasonal.",
        "parameters": {
            "type": "object",
            "properties": {
                "account_id": {
                    "type": "string",
                    "description": "The account to retrieve historical actuals for."
                },
                "current_period": {
                    "type": "string",
                    "description": "The reference period in YYYY-MM format. Prior periods are calculated relative to this."
                },
                "n": {
                    "type": "integer",
                    "description": "Number of prior periods to return. Defaults to 3."
                }
            },
            "required": ["account_id", "current_period"]
        }
    }
}

SUBMIT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "submit",
        "description": "Submit your final variance analysis. Call this when you have identified the action, driver, and grounding evidence. This ends the analysis.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["flag", "do_nothing", "escalate"]
                },
                "driver_type": {
                    "type": "string",
                    "enum": ["price_change", "one_time_item", "volume_change", 
                             "timing_accrual", "data_error", "none"]
                },
                "magnitude": {"type": "number"},
                "description": {"type": "string"},
                "confidence": {"type": "number"},
                "grounding": {
                    "type": "object",
                    "properties": {
                        "transaction_ids": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "signal": {"type": "string"}
                    },
                    "required": ["transaction_ids", "signal"]
                }
            },
            "required": ["action", "driver_type", "magnitude", 
                        "description", "confidence", "grounding"]
        }
    }
}

ALL_TOOLS = [
    QUERY_ACTUALS_SCHEMA,
    QUERY_BUDGET_SCHEMA,
    GET_TRANSACTIONS_SCHEMA,
    GET_PRIOR_PERIODS_SCHEMA,
    SUBMIT_SCHEMA,
]

TOOL_FUNCTIONS = {
    "query_actuals": query_actuals,
    "query_budget": query_budget,
    "get_transactions": get_transactions,
    "get_prior_periods": get_prior_periods,
}
    






    




