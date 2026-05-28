"""Conexão com o banco de dados via psycopg2."""

import psycopg2
from psycopg2.extras import RealDictCursor

_CONFIG = {
    "dbname": "vscode",
    "user": "vscode",
    "host": "/var/run/postgresql",
    "port": 5432,
    "options": "-c search_path=carteiras_wm",
}


def get_conn():
    """Retorna uma nova conexão com o banco de dados."""
    return psycopg2.connect(**_CONFIG)


def query(sql, params=None):
    """Executa SELECT e retorna lista de dicts."""
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]


def execute(sql, params=None):
    """Executa DML (INSERT/UPDATE/DELETE) e retorna rowcount."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rowcount = cur.rowcount
        conn.commit()
    return rowcount


def execute_returning(sql, params=None):
    """Executa INSERT ... RETURNING e retorna o primeiro registro."""
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
        conn.commit()
    return dict(row) if row else None


def explain(sql, params=None, analyze=True):
    """Retorna o plano de execução como string."""
    prefix = "EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)" if analyze else "EXPLAIN"
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"{prefix} {sql}", params)
            rows = cur.fetchall()
    return "\n".join(r[0] for r in rows)
