import os
import psycopg
from dotenv import load_dotenv
import uuid
from evals.schemas import AgentOutput
from core.loop import RunUsage

load_dotenv()

CREATE_TABLE_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS case_memory (
    id          SERIAL PRIMARY KEY,
    case_id     TEXT NOT NULL,
    period      TEXT NOT NULL,
    account_id  TEXT NOT NULL,
    confirmed_driver  TEXT NOT NULL,
    confirmed_action  TEXT NOT NULL,
    description TEXT NOT NULL,
    domain      TEXT NOT NULL DEFAULT 'fpa',
    embedding   vector(384) NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS case_memory_embedding_idx
    ON case_memory
    USING hnsw (embedding vector_cosine_ops);
"""

RUNS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS runs (
    id                SERIAL PRIMARY KEY,
    run_id            TEXT NOT NULL,
    case_id           TEXT NOT NULL,
    domain            TEXT NOT NULL DEFAULT 'fpa',
    action            TEXT NOT NULL,
    driver_type       TEXT NOT NULL,
    magnitude         FLOAT,
    confidence        FLOAT,
    description       TEXT,
    prompt_tokens     INT,
    completion_tokens INT,
    llm_calls         INT,
    cost_usd          FLOAT,
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    reviewed_at       TIMESTAMPTZ,
    confirmed_action  TEXT,
    confirmed_driver  TEXT,
    reviewer_note     TEXT
);
"""

def persist_run(output: AgentOutput, usage: RunUsage, domain: str = "fpa") -> str:
    """Write one agent run to the runs table. Returns the run_id."""
    run_id = str(uuid.uuid4())
    url = os.getenv("DATABASE_URL")
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO runs (
                    run_id, case_id, domain,
                    action, driver_type, magnitude, confidence, description,
                    prompt_tokens, completion_tokens, llm_calls, cost_usd
                ) VALUES (
                    %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
            """, (
                run_id, output.case_id, domain, output.action, output.driver_type
                ,output.magnitude, output.confidence, output.description,
                usage.prompt_tokens, usage.completion_tokens, usage.llm_calls,
                usage.cost_usd
            ))
        conn.commit()
    return run_id

def init_db():
    url = os.getenv("DATABASE_URL")
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
            cur.execute(RUNS_TABLE_SQL)
        conn.commit()
    print("tables ready")

if __name__ == "__main__":
    init_db()