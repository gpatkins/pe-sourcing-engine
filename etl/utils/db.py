"""
Database connection utilities for PE Sourcing Engine v5.1
Updated for psycopg3 compatibility with Python 3.14
"""

from __future__ import annotations
import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from pathlib import Path

# Points to /opt/pe-sourcing-engine/config/secrets.env
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / "config" / "secrets.env"
load_dotenv(ENV_PATH)


def get_db_connection():
    """
    Creates a connection to the database defined in secrets.env.
    Returns a psycopg3 connection object.
    
    Returns:
        psycopg.Connection: Database connection
    """
    return psycopg.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", "5432")
    )


def get_connection():
    """
    Alias for get_db_connection() for backward compatibility.
    Creates a connection to the database defined in secrets.env.
    
    Returns:
        psycopg.Connection: Database connection
    """
    return get_db_connection()


def execute(sql: str, params: tuple | dict = None):
    """
    Helper for single-shot updates (auto-commits).
    
    Args:
        sql: SQL query string
        params: Query parameters (tuple or dict)
    """
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
            conn.commit()
    finally:
        conn.close()


def fetch_all_dict(sql: str, params: tuple | dict = None):
    """
    Helper to fetch rows as dictionaries.
    
    Args:
        sql: SQL query string
        params: Query parameters (tuple or dict)
        
    Returns:
        list[dict]: List of rows as dictionaries
    """
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, params)
                return cur.fetchall()
    finally:
        conn.close()


def fetch_one_dict(sql: str, params: tuple | dict = None):
    """
    Helper to fetch a single row as a dictionary.
    
    Args:
        sql: SQL query string
        params: Query parameters (tuple or dict)
        
    Returns:
        dict | None: Single row as dictionary or None if no results
    """
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, params)
                return cur.fetchone()
    finally:
        conn.close()


def test_connection():
    """
    Test database connection.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        print(f"Database connection test failed: {e}")
        return False
