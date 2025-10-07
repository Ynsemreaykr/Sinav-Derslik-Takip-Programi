# services/db.py
from typing import Any, Iterable, Sequence
from database.connection import get_conn_cursor

def fetch_all(sql: str, params: Sequence[Any] | None = None) -> list[dict]:
    with get_conn_cursor() as (_, cur):
        cur.execute(sql, params or [])
        return list(cur.fetchall())

def fetch_one(sql: str, params: Sequence[Any] | None = None) -> dict | None:
    with get_conn_cursor() as (_, cur):
        cur.execute(sql, params or [])
        row = cur.fetchone()
        return dict(row) if row else None

def execute(sql: str, params: Sequence[Any] | None = None) -> int:
    with get_conn_cursor() as (conn, cur):
        cur.execute(sql, params or [])
        return cur.rowcount

def executemany(sql: str, seq_of_params: Iterable[Sequence[Any]]) -> int:
    with get_conn_cursor() as (conn, cur):
        cur.executemany(sql, seq_of_params)
        return cur.rowcount
