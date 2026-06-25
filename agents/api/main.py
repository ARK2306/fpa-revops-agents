from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import psycopg, os
from datetime import datetime, timezone
from core.memory import store

load_dotenv()
app = FastAPI()

def get_db():
    return psycopg.connect(os.getenv("DATABASE_URL"))

# --- GET endpoint (given) ---
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