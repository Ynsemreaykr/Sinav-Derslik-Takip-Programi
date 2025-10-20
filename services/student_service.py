# services/student_service.py
from typing import List, Optional
from database.db import fetch_all, fetch_one, execute
from models.student import Student

def get_all_by_department(department_id: int) -> List[Student]:
    rows = fetch_all(
        "SELECT * FROM students WHERE department_id = %s ORDER BY number",
        [department_id]
    )
    return [Student.from_row(r) for r in rows]

def get_by_id(student_id: int) -> Optional[Student]:
    row = fetch_one("SELECT * FROM students WHERE id = %s", [student_id])
    return Student.from_row(row) if row else None

def create(s: Student) -> int:
    return execute("""
        INSERT INTO students (department_id, number, fullname, grade)
        VALUES (%s, %s, %s, %s)
    """, [s.department_id, s.number, s.fullname, s.grade])

def update(s: Student) -> int:
    return execute("""
        UPDATE students
           SET number=%s, fullname=%s, grade=%s
         WHERE id=%s
    """, [s.number, s.fullname, s.grade, s.id])

def delete(student_id: int) -> int:
    return execute("DELETE FROM students WHERE id = %s", [student_id])
