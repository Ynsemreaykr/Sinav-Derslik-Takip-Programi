# services/enrollment_service.py
from typing import List
from database.db import fetch_all, execute

def enroll_student(student_id: int, course_id: int) -> int:
    """Öğrenciyi derse kaydeder."""
    return execute("""
        INSERT INTO enrollments (student_id, course_id)
        VALUES (%s, %s)
        ON CONFLICT (student_id, course_id) DO NOTHING
    """, [student_id, course_id])

def get_courses_of_student(student_id: int) -> List[dict]:
    """Bir öğrencinin aldığı dersleri getir."""
    return fetch_all("""
        SELECT c.*
        FROM enrollments e
        JOIN courses c ON c.id = e.course_id
        WHERE e.student_id = %s
        ORDER BY c.code
    """, [student_id])

def get_students_in_course(course_id: int) -> List[dict]:
    """Bir dersi alan öğrencileri getir."""
    return fetch_all("""
        SELECT s.*
        FROM enrollments e
        JOIN students s ON s.id = e.student_id
        WHERE e.course_id = %s
        ORDER BY s.number
    """, [course_id])

def remove_enrollment(student_id: int, course_id: int) -> int:
    """Bir öğrenciyi dersten çıkar."""
    return execute("""
        DELETE FROM enrollments
         WHERE student_id = %s AND course_id = %s
    """, [student_id, course_id])
