# database/db.py
from typing import Any, List, Optional
from database.connection import get_conn_cursor

# Örnek kullanım MANTIK BURDA
# from database.db import fetch_all, execute
#
# # Tüm öğrencileri getir
# students = fetch_all("SELECT * FROM students")
#
# # Yeni öğrenci ekle
# execute(
#     "INSERT INTO students (department_id, number, fullname, grade) VALUES (%s, %s, %s, %s)",
#     [1, '220101001', 'Ahmet Yılmaz', 3]
# )

# =========================================================
# Temel DB yardımcı fonksiyonları (context yönetimli)
# =========================================================

def fetch_all(query: str, params: Optional[List[Any]] = None) -> List[dict]:
    """Tüm satırları getir (SELECT)"""
    with get_conn_cursor() as (_, cur):
        cur.execute(query, params or [])
        return cur.fetchall()


def fetch_one(query: str, params: Optional[List[Any]] = None) -> Optional[dict]:
    """Tek bir satır döndür (örneğin LIMIT 1 sorgularında)"""
    with get_conn_cursor() as (_, cur):
        cur.execute(query, params or [])
        return cur.fetchone()


def execute(query: str, params: Optional[List[Any]] = None) -> int:
    """
    INSERT / UPDATE / DELETE sorguları için.
    Dönen değer: etkilenen satır sayısı.
    """
    with get_conn_cursor() as (conn, cur):
        cur.execute(query, params or [])
        affected = cur.rowcount
        return affected


def executemany(query: str, param_list: List[List[Any]]) -> int:
    """
    Toplu işlem (ör: birden fazla kayıt ekleme)
    """
    with get_conn_cursor() as (conn, cur):
        cur.executemany(query, param_list)
        affected = cur.rowcount
        return affected
