# services/db.py
from typing import Any, Iterable, Sequence
from database.connection import get_conn_cursor

def fetch_all(sql: str, params: Sequence[Any] | None = None) -> list[dict]:
    """Birden fazla kayıt döner."""
    with get_conn_cursor() as (_, cur):
        cur.execute(sql, params or [])
        return list(cur.fetchall())

def fetch_one(sql: str, params: Sequence[Any] | None = None) -> dict | None:
    """Tek kayıt döner."""
    with get_conn_cursor() as (_, cur):
        cur.execute(sql, params or [])
        row = cur.fetchone()
        return dict(row) if row else None

def execute(sql: str, params: Sequence[Any] | None = None, return_id: bool = False) -> int:
    with get_conn_cursor() as (conn, cur):
        cur.execute(sql, params or [])
        conn.commit()
        
        if return_id:
            # RETURNING id kullanan INSERT sorgularında
            result = cur.fetchone()
            return result['id'] if result else None
        
        return cur.rowcount


def executemany(sql: str, seq_of_params: Iterable[Sequence[Any]]) -> int:
    """Çoklu kayıt ekleme."""
    with get_conn_cursor() as (_, cur):
        cur.executemany(sql, seq_of_params)
        return cur.rowcount
