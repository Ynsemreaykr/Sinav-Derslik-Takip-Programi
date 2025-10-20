# services/course_service.py
from typing import List, Optional
from database.db import fetch_all, fetch_one, execute
from models.course import Course

def get_all_by_department(department_id: int) -> List[Course]:
    rows = fetch_all(
        "SELECT * FROM courses WHERE department_id = %s ORDER BY grade, code",
        [department_id]
    )
    return [Course.from_row(r) for r in rows]

def get_by_id(course_id: int) -> Optional[Course]:
    row = fetch_one("SELECT * FROM courses WHERE id = %s", [course_id])
    return Course.from_row(row) if row else None

def create(c: Course) -> int:
    return execute("""
        INSERT INTO courses (department_id, code, name, instructor, grade, is_elective)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, [c.department_id, c.code, c.name, c.instructor, c.grade, c.is_elective])

def delete(course_id: int) -> int:
    return execute("DELETE FROM courses WHERE id = %s", [course_id])
