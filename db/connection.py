"""
db/connection.py
PostgreSQL connection pool for the Agentic Hackathon project.

Loads credentials from D:/TheCraftersHub_DataLab/.env (Cabinet .env).
Registers pgvector extension on every connection.

Usage:
    from db.connection import get_connection, test_connection

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
"""

import os
import logging
from contextlib import contextmanager

import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv

# ── Load .env ─────────────────────────────────────────────────────────────────
# Primary: Cabinet .env (production secrets)
load_dotenv("D:/TheCraftersHub_DataLab/.env")
# Secondary: local .env in repo root (overrides nothing by default)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"), override=False)

logger = logging.getLogger(__name__)

# ── Build DATABASE_URL ────────────────────────────────────────────────────────
def _build_dsn() -> str:
    """Construct a DSN string from env vars."""
    explicit = os.getenv("DATABASE_URL")
    if explicit:
        return explicit

    user     = os.getenv("POSTGRES_USER", "crafter_admin")
    password = os.getenv("POSTGRES_PASSWORD", "")
    host     = os.getenv("POSTGRES_HOST", "localhost")
    port     = os.getenv("POSTGRES_PORT", "5432")
    db       = os.getenv("POSTGRES_DB", "thecraftershub")

    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


DSN = _build_dsn()

# ── Connection pool (lazy init) ───────────────────────────────────────────────
_pool: psycopg2.pool.SimpleConnectionPool | None = None


def _get_pool() -> psycopg2.pool.SimpleConnectionPool:
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            dsn=DSN,
        )
        logger.debug("PostgreSQL connection pool created (min=1, max=5)")
    return _pool


# ── Public interface ──────────────────────────────────────────────────────────
@contextmanager
def get_connection():
    """
    Context manager that yields a psycopg2 connection from the pool.
    Commits on clean exit, rolls back on exception.
    Always returns the connection to the pool.

    Example:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
    """
    pool = _get_pool()
    conn = pool.getconn()

    # register_vector requires autocommit=True (no open transaction)
    conn.autocommit = True
    register_vector(conn)
    conn.autocommit = False  # switch to manual commit for safe writes

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        # Reset state before returning to pool
        try:
            conn.autocommit = False
        except Exception:
            pass
        pool.putconn(conn)


@contextmanager
def get_dict_connection():
    """
    Like get_connection() but yields a connection whose cursors return
    rows as dictionaries (RealDictCursor).
    """
    pool = _get_pool()
    conn = pool.getconn()
    conn.autocommit = True
    register_vector(conn)
    conn.autocommit = False

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        try:
            conn.autocommit = False
        except Exception:
            pass
        pool.putconn(conn)


def test_connection() -> bool:
    """
    Returns True if the database is reachable, False otherwise.
    Safe to call at startup.
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                return result is not None
    except Exception as e:
        logger.error(f"DB connection test failed: {e}")
        return False
