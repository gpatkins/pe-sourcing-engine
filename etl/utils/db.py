from __future__ import annotations
import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from pathlib import Path

# Points to /opt/pe-sourcing-engine/config/secrets.env
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / "config" / "secrets.env"
load_dotenv(ENV_PATH)

def get_connection():
    """Creates a connection to the database defined in secrets.env"""
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", "5432")
    )

def execute(sql: str, params: tuple | dict = None):
    """Helper for single-shot updates (auto-commits)"""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
    finally:
        conn.close()

def fetch_all_dict(sql: str, params: tuple | dict = None):
    """Helper to fetch rows as dictionaries"""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, params)
                return cur.fetchall()
    finally:
        conn.close()
