import os
import psycopg
from dotenv import load_dotenv

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
    embedding   vector(384) NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS case_memory_embedding_idx
    ON case_memory
    USING hnsw (embedding vector_cosine_ops);
"""

def init_db():
    url = os.getenv("DATABASE_URL")
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
        conn.commit()
    print("table ready")

if __name__ == "__main__":
    init_db()