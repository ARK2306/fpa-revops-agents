import os
import numpy as np
import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

load_dotenv()

model = SentenceTransformer("all-MiniLM-L6-v2")

def embed(text: str) -> list[float]:
    return model.encode(text).tolist()

def store(case_text: str, case_id: str, period: str, account_id: str,
          confirmed_driver: str, confirmed_action: str,
          description: str, domain: str = "fpa"):
    vector = embed(case_text)
    url = os.getenv("DATABASE_URL")
    with psycopg.connect(url) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO case_memory
                    (case_id, period, account_id, confirmed_driver,
                     confirmed_action, description, embedding, domain)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (case_id, period, account_id, confirmed_driver,
                  confirmed_action, description, np.array(vector), domain))
        conn.commit()

def retrieve(query_text: str, domain: str = "fpa", k: int = 3) -> list[dict]:
    vector = embed(query_text)
    query_vector = np.array(vector)
    url = os.getenv("DATABASE_URL")
    with psycopg.connect(url) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT case_id, confirmed_driver, confirmed_action, description
                FROM case_memory
                WHERE domain = %s
                ORDER BY embedding <=> %s
                LIMIT %s
            """, (domain, query_vector, k))
            rows = cur.fetchall()
    return [
        {
            "case_id": row[0],
            "confirmed_driver": row[1],
            "confirmed_action": row[2],
            "description": row[3],
        }
        for row in rows
    ]