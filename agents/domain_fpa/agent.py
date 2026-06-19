from evals.schemas import AgentOutput, CaseInput
from core.loop import run_agent
from domain_fpa.tools import ALL_TOOLS, TOOL_FUNCTIONS
import json

SYSTEM_PROMPT = """
You are an FP&A variance analysis agent. Analyze actual vs budget data and identify material variances with grounded evidence.

## Materiality thresholds (OR rule — either triggers action)
- Absolute variance >= $25,000
- Percentage variance >= 15% of budget

## Workflow — follow this order
1. Call query_actuals and query_budget for the period to compute variance
2. If variance is material, call get_transactions to see individual rows
3. Optionally call get_prior_periods to distinguish spike vs trend
4. Call submit with your findings

## Actions
- flag: variance is material AND you can identify the driver from transaction evidence
- escalate: variance is material BUT driver is unclear, data looks incomplete, or transactions have date/period mismatches requiring human confirmation
- do_nothing: variance is not material (fails both thresholds)

## Driver types
- price_change: all transactions systematically higher/lower than expected
- volume_change: more or fewer transactions than normal
- one_time_item: single anomalous transaction not in budget
- timing_accrual: transactions dated in a different period than they are posted to
- data_error: transactions miscoded to wrong account (description doesn't match account)
- none: no material variance

## Grounding rule — CRITICAL
Every flag or escalate MUST cite specific transaction_ids as evidence.
If you cannot point to specific rows that explain the variance, escalate instead of guessing.
do_nothing requires no driver — set driver_type to "none".

## Confidence
- 0.9-1.0: clear evidence, single obvious driver
- 0.5-0.8: material variance but driver is inferred, not certain
- 0.0-0.4: escalating because evidence is ambiguous
"""

def run_fpa_agent(case_id: str, case_input: CaseInput) -> AgentOutput:
    transactions_json = json.dumps(
    [t.model_dump() for t in case_input.transactions],
    indent=2,
    default=str
)
    user_message = f"""
Analyze this period for material variances:
- Period: {case_input.period}
- Account: {case_input.account_id}
- Budget: {case_input.budget}
- Transactions provided: {len(case_input.transactions)}

Transactions:
{transactions_json}

Start by calling query_actuals and query_budget to compute the variance, then get_transactions to find the driver. Submit your findings using the submit tool.
"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]
    
    return run_agent(
        case_id=case_id,
        messages=messages,
        tools=ALL_TOOLS,
        tool_functions=TOOL_FUNCTIONS
    )