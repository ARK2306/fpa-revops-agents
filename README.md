# FP&A Variance Agent

An industry-grade AI agent that classifies GL account variances by driver type, recommends actions, and grounds every claim in transaction-level evidence. Built as a portfolio demonstration of production agent engineering patterns.

**Live demo:** https://fpa-revops-agents.vercel.app  
**API:** https://fpa-api-182571398865.us-central1.run.app

---

## What it does

Upload a GL export CSV from any accounting system (QuickBooks, NetSuite, SAP, Sage), map your column headers once, and the agent:

1. Queries actuals, budget, and transaction history via tool calls
2. Classifies the variance driver: `price_change`, `volume_change`, `one_time_item`, `timing_accrual`, `data_error`, or `none`
3. Recommends an action: `flag`, `escalate`, or `do_nothing`
4. Grounds every claim in specific transaction IDs — no grounding, no confident answer
5. Learns from human-reviewed outcomes via vector memory (pgvector)

Multi-turn chat lets analysts ask follow-up questions. A **Deep Dive** toggle re-runs tool calls on follow-up turns for fresh data rather than reasoning from memory.

---

## Measured performance

All metrics produced by the eval runner on 23 golden cases with an independent LLM judge (`nvidia/nemotron-3-super-120b-a12b` — different model family from the agent).

| Metric                    | Empty memory | 21 cases seeded |
| ------------------------- | ------------ | --------------- |
| Action accuracy           | 0.913        | 0.913           |
| Escalate recall           | 0.890        | 0.890           |
| Driver mean (judge score) | 0.870        | 0.890           |
| Avg cost / run            | ~$0.0012     | ~$0.0012        |

**Grader effect:** 0.000 — Nemotron and DeepSeek judges agreed on all 19 scoreable cases when grading identical frozen outputs.

**Memory effect:** action accuracy held flat; driver classification quality improved +0.020 with seeded memory. Memory improves explanation precision, not binary action decisions at this scale.

**Known limitations:**

- fpa_026 is a permanent boundary case — the agent classifies `price_change` where the golden label is `none` (requires prior period breakdown not available in the data)
- fpa_015 intermittently produces malformed tool call JSON (~1-in-23 rate) — handled by the grounding guardrail, escalates safely
- Single-run checkpoint variance is ±1 case (~4%) at n=23 — numbers are not averaged across runs

---

## Architecture

```
frontend/          React + Tailwind (Vercel)
agents/
  api/
    main.py        FastAPI — POST /analyze, POST /chat, GET /runs, POST /runs/{id}/review
  core/
    loop.py        Agent loop — tool calling, grounding guardrail, malformed-output recovery
    llm_client.py  OpenRouter client — DeepSeek via provider pin, tenacity retries
    memory.py      pgvector store/retrieve (k=3 precedents)
  domain_fpa/
    agent.py       FP&A agent entry point
    tools.py       GL tools — query_actuals, query_budget, get_transactions, get_prior_periods
    normalizer.py  CSV column mapping — normalize any GL export to agent schema
  memory/
    store.py       Runs table persistence, HITL review writes to case_memory
  evals/
    runner.py      23-case golden set eval with 3-class confusion matrix
    grade_frozen.py  Grader-effect experiment — freeze outputs, vary judge only
    freeze_outputs.py  Serialize agent outputs for offline grading
```

### Agent loop

```
system prompt + k=3 memory precedents
        ↓
LLM decides which tool to call
        ↓
tool executes → result appended to messages
        ↓
repeat until submit() called
        ↓
grounding guardrail: if no transaction IDs cited → escalate
        ↓
AgentOutput + RunUsage returned
```

### Key engineering decisions

**Grounding is load-bearing.** Every driver claim must cite specific transaction IDs. If the agent calls `submit()` with an empty grounding list, the loop overrides the action to `escalate`. A correct action with wrong grounding is a fragile correct.

**escalate > flag, never the reverse.** The asymmetric error policy is enforced in the system prompt and the grounding guardrail. A false escalation wastes analyst time. A missed escalation hides a real problem.

**Independent judge.** The eval runner uses Nemotron (different model family) to score driver quality. Same-model judging inflates scores. The grader-effect experiment confirmed 0.000 bias before locking the judge.

**do_nothing confirmations never written to memory.** Only confirmed flag/escalate HITL reviews write to `case_memory`. No useful signal from confirmed do_nothing.

**Session-aware tools.** Uploaded CSV data is stored in a module-level dict keyed by session_id. Tool functions check the current session before falling back to static data files. No signature changes to tool functions — a context variable carries the session.

---

## Stack

| Component     | Technology                                         |
| ------------- | -------------------------------------------------- |
| LLM           | DeepSeek via OpenRouter (provider-pinned)          |
| Eval judge    | Nvidia Nemotron 120B (independent family)          |
| Observability | Langfuse v4.x (`@observe`, `propagate_attributes`) |
| Vector memory | pgvector + PostgreSQL (psycopg3)                   |
| API           | FastAPI                                            |
| Frontend      | React + Tailwind (Vite)                            |
| Database      | Supabase (PostgreSQL 15 + pgvector)                |
| Deploy        | Google Cloud Run (API) + Vercel (frontend)         |
| Dependencies  | uv                                                 |

---

## Running locally

**Prerequisites:** Docker, Python 3.12+, uv, Node 20+

```bash
# clone
git clone https://github.com/ARK2306/fpa-revops-agents
cd fpa-revops-agents

# start postgres + pgvector
docker compose up -d

# install dependencies
cd agents && uv sync

# copy and fill env vars
cp .env.example .env

# init database
python -m memory.store

# seed memory pool (optional)
python -m domain_fpa.memory

# start API
uvicorn api.main:app --reload --port 8000

# start frontend (separate terminal)
cd ../frontend && npm install && npm run dev
```

Open http://localhost:3000

**Run evals:**

```bash
cd agents
python -m evals.runner           # full 23-case eval
python -m evals.runner --cases fpa_001 fpa_002 fpa_003   # fast subset
```

---

## CSV format

Upload any GL export. The column mapping UI lets you map your column names to the required schema:

| Required field   | Example column names             |
| ---------------- | -------------------------------- |
| `transaction_id` | Doc No, Entry Number, TxnId      |
| `account_id`     | Account, GL Account, AccountCode |
| `date`           | Date, Transaction Date, TxnDate  |
| `amount`         | Amount, Debit, Net Amount        |
| `description`    | Memo, Details, Description       |
| `period`         | auto-derived from date (YYYY-MM) |

Compatible with any GL system that exports CSV: QuickBooks, NetSuite, SAP, Sage, Xero.

---

## Extensibility

**Second GL system:** add a normalizer function in `domain_fpa/normalizer.py`. The agent tools are data-source agnostic — they read from a normalized dataframe regardless of origin.

**QuickBooks direct integration:** tool signatures are designed to be MCP-compatible. Swap `TOOL_FUNCTIONS` dict entries to call QuickBooks MCP tools directly. Column mapping becomes `normalize_qbo()` with a fixed field mapping.

**Multi-user support:** `_sessions` dict in `api/main.py` is in-memory and single-tenant. Production path: replace with Redis-backed sessions keyed by user_id + JWT auth middleware.

**RevOps Deal-Risk Agent:** ~80% of `core/` is domain-agnostic. The second agent reuses `loop.py`, `llm_client.py`, `memory.py`, and the eval infrastructure. Only `domain_fpa/` is replaced with `domain_revops/`.

---

## Evaluation methodology

- **Golden set:** 23 hand-labeled cases covering all 5 driver types + escalation boundary cases
- **Memory pool:** 21 seeded cases, strictly disjoint from golden set (no signal overlap)
- **Scoring:** 3-class confusion matrix (do_nothing / flag / escalate) for action; LLM-as-judge for driver quality (0 / 0.5 / 1.0)
- **Judge independence:** grader-effect experiment freezes agent outputs and varies only the judge — isolates judge bias from agent behavior
- **Checkpoint method:** single runs with documented ±1 case variance caveat; no 3x averaging

---

## Cost

~$0.0012 per analysis run (4-7 LLM calls via OpenRouter).  
Eval suite (23 cases + judge): ~$0.05 per full run.
