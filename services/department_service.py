# services/department_service.py
from typing import List, Optional
from database.db import fetch_all, fetch_one, execute
from models.department import Department

def get_all() -> List[Department]:
    rows = fetch_all("SELECT * FROM departments ORDER BY id")
    return [Department.from_row(r) for r in rows]

def get_by_id(department_id: int) -> Optional[Department]:
    row = fetch_one("SELECT * FROM departments WHERE id = %s", [department_id])
    return Department.from_row(row) if row else None

def create(name: str) -> int:
    return execute("INSERT INTO departments (name) VALUES (%s)", [name])

def delete(department_id: int) -> int:
    return execute("DELETE FROM departments WHERE id = %s", [department_id])
