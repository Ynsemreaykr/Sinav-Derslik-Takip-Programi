# services/student_service.py
from typing import List, Optional
from services.db import fetch_all, fetch_one, execute
from models.student import Student

def list_students() -> List[Student]:
    rows = fetch_all("SELECT id, name, student_no, department_id, email FROM students ORDER BY id DESC")
    return [Student.from_row(r) for r in rows]

def get_student(sid: int) -> Optional[Student]:
    row = fetch_one("SELECT id, name, student_no, department_id, email FROM students WHERE id = %s", [sid])
    return Student.from_row(row) if row else None

def create_student(s: Student) -> int:
    sql = """
    INSERT INTO students (name, student_no, department_id, email)
    VALUES (%s, %s, %s, %s)
    """
    return execute(sql, [s.name, s.student_no, s.department_id, s.email])

def update_student(s: Student) -> int:
    sql = """
    UPDATE students
       SET name=%s, student_no=%s, department_id=%s, email=%s
     WHERE id=%s
    """
    return execute(sql, [s.name, s.student_no, s.department_id, s.email, s.id])

def delete_student(sid: int) -> int:
    return execute("DELETE FROM students WHERE id=%s", [sid])
