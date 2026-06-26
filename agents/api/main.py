from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import psycopg, os
from datetime import datetime, timezone
from core.memory import store
from domain_fpa.agent import run_fpa_agent
from memory.store import persist_run
from evals.schemas import LiveCaseInput
from fastapi import UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import io, json
import pandas as pd
from domain_fpa.tools import set_session, register_session_data
from domain_fpa.normalizer import normalize_csv
from core.llm_client import complete
from core.llm_client import complete_with_tools
from domain_fpa.tools import ALL_TOOLS, TOOL_FUNCTIONS

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_sessions: dict[str, dict] = {}


def get_db():
    return psycopg.connect(os.getenv("DATABASE_URL"))

@app.get("/runs")
def list_runs(limit: int = 20):
    keys = ["run_id", "case_id", "domain", "action", "driver_type",
            "confidence", "cost_usd", "created_at",
            "reviewed_at", "confirmed_action"]
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT run_id, case_id, domain, action, driver_type,
                       confidence, cost_usd, created_at,
                       reviewed_at, confirmed_action
                FROM runs
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
    result = []
    for row in rows:
        d = dict(zip(keys, row))
        d["created_at"] = d["created_at"].isoformat() if d["created_at"] else None
        d["reviewed_at"] = d["reviewed_at"].isoformat() if d["reviewed_at"] else None
        result.append(d)
    return result

@app.get("/runs/{run_id}")
def get_run(run_id: str):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT run_id, case_id, domain, action, driver_type,
                       magnitude, confidence, description,
                       prompt_tokens, completion_tokens, llm_calls, cost_usd,
                       created_at, reviewed_at, confirmed_action,
                       confirmed_driver, reviewer_note
                FROM runs WHERE run_id = %s
            """, (run_id,))
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="run not found")
    keys = ["run_id","case_id","domain","action","driver_type",
            "magnitude","confidence","description",
            "prompt_tokens","completion_tokens","llm_calls","cost_usd",
            "created_at","reviewed_at","confirmed_action",
            "confirmed_driver","reviewer_note"]
    return dict(zip(keys, row))



class ReviewRequest(BaseModel):
    confirmed_action: str
    confirmed_driver: str
    reviewer_note: str

@app.post("/runs/{run_id}/review")
def submit_review(run_id: str, body: ReviewRequest):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT case_id, domain FROM runs WHERE run_id = %s", (run_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="run not found")
            case_id, domain = row

            cur.execute("""
                UPDATE runs
                SET confirmed_action = %s,
                    confirmed_driver = %s,
                    reviewer_note    = %s,
                    reviewed_at      = NOW()
                WHERE run_id = %s
            """, (body.confirmed_action, body.confirmed_driver,
                  body.reviewer_note, run_id))
        conn.commit()

    if body.confirmed_action in ("flag", "escalate"):
        store(
    case_text=f"{case_id}: {body.confirmed_driver} — {body.reviewer_note}",
    case_id=case_id,
    period="unknown",
    account_id="unknown",
    confirmed_driver=body.confirmed_driver,
    confirmed_action=body.confirmed_action,
    description=body.reviewer_note,
    domain=domain,
)

    return get_run(run_id)

class AnalyzeRequest(BaseModel):
    account_id: str
    period: str
    budget: float

@app.post("/analyze")
def analyze(body: AnalyzeRequest):
    case_id = f"live_{body.account_id}_{body.period}".replace(" ", "_")
    case_input = LiveCaseInput(
        account_id=body.account_id,
        period=body.period,
        budget=body.budget
    )
    try:
        output, usage = run_fpa_agent(case_id, case_input)
        run_id = persist_run(output, usage)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "run_id": run_id,
        "case_id": case_id,
        "action": output.action,
        "driver_type": output.driver_type,
        "magnitude": output.magnitude,
        "confidence": output.confidence,
        "description": output.description,
        "grounding": {
            "transaction_ids": output.grounding.transaction_ids,
            "signal": output.grounding.signal
        },
        "cost_usd": usage.cost_usd,
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "llm_calls": usage.llm_calls
    }

@app.post("/chat")
async def chat(
    session_id: str = Form(...),
    deep_dive: str = Form(default="false"),
    message: str = Form(...),
    account_id: str = Form(default=""),
    period: str = Form(default=""),
    budget: float = Form(default=0.0),
    column_mapping: str = Form(default="{}"),
    file: UploadFile | None = File(default=None)
):
    if session_id not in _sessions:
        _sessions[session_id] = {"history": [], "agent_output": None}

    session = _sessions[session_id]

    # first message — run the agent
    if session["agent_output"] is None:
        if file:
            contents = await file.read()
            raw_df = pd.read_csv(io.BytesIO(contents))
            mapping = json.loads(column_mapping)
            try:
                normalized = normalize_csv(raw_df, mapping)
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
            register_session_data(session_id, normalized)

        set_session(session_id)

        case_id = f"chat_{session_id[:8]}"
        case_input = LiveCaseInput(
            account_id=account_id,
            period=period,
            budget=budget
        )

        try:
            output, usage = run_fpa_agent(case_id, case_input)
            run_id = persist_run(output, usage)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        agent_result = {
            "run_id": run_id,
            "action": output.action,
            "driver_type": output.driver_type,
            "magnitude": output.magnitude,
            "confidence": output.confidence,
            "description": output.description,
            "grounding": {
                "transaction_ids": output.grounding.transaction_ids,
                "signal": output.grounding.signal
            },
            "cost_usd": usage.cost_usd,
            "llm_calls": usage.llm_calls
        }
        session["agent_output"] = agent_result
        session["account_id"] = account_id
        session["period"] = period
        session["history"] = [{
            "role": "assistant",
            "content": (
                f"Analysis complete.\n"
                f"Action: {output.action.upper()}\n"
                f"Driver: {output.driver_type}\n"
                f"Confidence: {output.confidence}\n"
                f"Magnitude: ${output.magnitude:,.0f}\n"
                f"Description: {output.description}\n"
                f"Grounding: "
                f"{', '.join(output.grounding.transaction_ids) or 'none cited'}"
            )
        }]

        return {"type": "agent_output", "data": agent_result}


    session["history"].append({"role": "user", "content": message})

    if deep_dive == "true":
        # tool-calling follow-up — mini agent run with session context
        set_session(session_id)
        stored = session["agent_output"]
        
        followup_messages = [
            {
                "role": "system",
                "content": (
                    f"You are an FP&A analyst assistant. You already analyzed "
                    f"account {session.get('account_id', 'unknown')} for period "
                    f"{session.get('period', 'unknown')}. "
                    f"Prior finding: {stored['action'].upper()} — "
                    f"{stored['driver_type']} — {stored['description'][:200]}. "
                    f"The user has a follow-up question. Use the available tools "
                    f"to answer it precisely with fresh data. "
                    f"Do not repeat the original analysis unless asked."
                )
            },
            {"role": "user", "content": message}
        ]
        
        tool_message, usage = complete_with_tools(followup_messages, ALL_TOOLS)
        
        # execute any tool calls
        tool_results = []
        if tool_message.tool_calls:
            for tc in tool_message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                    result = TOOL_FUNCTIONS[tc.function.name](**args)
                    tool_results.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result)
                    })
                except Exception as e:
                    tool_results.append({
                        "role": "tool", 
                        "tool_call_id": tc.id,
                        "content": f"error: {e}"
                    })
        
        # get final answer with tool results
        if tool_results:
            final_messages = followup_messages + [
                {"role": "assistant", "content": "", 
                "tool_calls": tool_message.tool_calls},
            ] + tool_results
            reply = complete(final_messages)
        else:
            reply = tool_message.content or "No tool results returned."

    else:
        # plain LLM chat
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an FP&A analyst assistant. The user has just received "
                    "a variance analysis from an AI agent. Answer follow-up questions "
                    "concisely and accurately. Do not invent transaction data not "
                    "present in the analysis. If you don't know, say so."
                )
            }
        ] + session["history"]
        reply = complete(messages)

    session["history"].append({"role": "assistant", "content": reply})
    return {"type": "chat_reply", "data": {"message": reply}}