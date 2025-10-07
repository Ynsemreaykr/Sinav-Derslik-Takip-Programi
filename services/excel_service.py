# services/excel_service.py
import pandas as pd
from typing import Iterable
from services.db import executemany

REQUIRED_COLS = ["name", "student_no", "department_id", "email"]

def _validate_df(df: pd.DataFrame):
    miss = [c for c in REQUIRED_COLS if c not in df.columns]
    if miss:
        raise ValueError(f"Excel kolonları eksik: {miss}")

def import_students_from_excel(path: str) -> int:
    df = pd.read_excel(path)  # engine=openpyxl otomatik seçilir
    _validate_df(df)
    rows: Iterable[tuple] = (
        (r["name"], r["student_no"], int(r["department_id"]), r.get("email"))
        for _, r in df.iterrows()
    )
    sql = "INSERT INTO students (name, student_no, department_id, email) VALUES (%s, %s, %s, %s)"
    return executemany(sql, rows)
