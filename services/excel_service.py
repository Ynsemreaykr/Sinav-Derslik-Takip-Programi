# services/excel_service.py
import pandas as pd
from typing import Optional
from services.db import fetch_all, execute

def _clean_excel_data(df: pd.DataFrame) -> pd.DataFrame:
    """Excel dosyasını temizle."""
    df = df.dropna(how="all")
    if len(df) > 1:
        df.columns = df.iloc[0]
        df = df.drop(df.index[0])
        df = df.reset_index(drop=True)
    return df

def import_departments():
    departments = [
        "Bilgisayar Muhendisligi",
        "Yazilim Muhendisligi",
        "Elektrik Muhendisligi",
        "Elektronik Muhendisligi",
        "Insaat Muhendisligi"
    ]
    for name in departments:
        existing = fetch_all("SELECT id FROM departments WHERE name = %s", [name])
        if not existing:
            execute("INSERT INTO departments (name) VALUES (%s)", [name])

def get_department_id(department_name: str) -> int:
    result = fetch_all("SELECT id FROM departments WHERE name = %s", [department_name])
    if result:
        return result[0]['id']
    # En az bir departman olmalı; seed edilmediyse fallback:
    return 1


def _normalize_turkish(text: str) -> str:
    """Türkçe karakterleri normalize et (ı->i, ş->s, İ->i, Ş->s vb.)"""
    replacements = {
        'İ': 'i', 'I': 'i',
        'Ş': 's', 'Ğ': 'g', 'Ü': 'u', 
        'Ö': 'o', 'Ç': 'c',
        'ı': 'i', 'ş': 's', 'ğ': 'g', 
        'ü': 'u', 'ö': 'o', 'ç': 'c'
    }
    for tr_char, en_char in replacements.items():
        text = text.replace(tr_char, en_char)
    return text.lower()

def import_courses_from_excel(path: str, department_id: Optional[int] = None) -> int:
    try:
        df = pd.read_excel(path, header=None)
    except Exception as e:
        raise ValueError(f"Excel okunamadı: {e}")

    if len(df.columns) >= 3:
        df.columns = ["code", "name", "instructor"]
    else:
        raise ValueError("Excel sütunları eksik. En az 3 sütun bekleniyor: code | name | instructor")

    df = df.fillna("")
    df["code"] = df["code"].astype(str).str.strip()
    df["name"] = df["name"].astype(str).str.strip()
    df["instructor"] = df["instructor"].astype(str).str.strip()

    added = 0
    dept_id = department_id if department_id is not None else get_department_id("Bilgisayar Muhendisligi")

    current_grade = 1
    current_is_elective = False

    for idx, row in df.iterrows():
        code = str(row["code"]).strip()
        name = str(row["name"]).strip()
        instructor = str(row.get("instructor", "")).strip()

        normalized = _normalize_turkish(code)

        if "secmeli" in normalized or "secimlik" in normalized:
            current_is_elective = True
            continue

        for n in range(1, 6):
            if f"{n}." in normalized and "sinif" in normalized:
                current_grade = n
                current_is_elective = False
                break

        if not code or code.upper() in ("DERS KODU", "CODE", "DERS"):
            continue

        if "sinif" in normalized:
            continue

        existing = fetch_all("SELECT id FROM courses WHERE department_id=%s AND code=%s", [dept_id, code])
        if not existing:
            execute("""
                INSERT INTO courses (department_id, code, name, instructor, grade, is_elective)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [dept_id, code, name, instructor, current_grade, current_is_elective])
            added += 1

    if department_id:
        update_student_enrollments_for_department(department_id)
    
    return added


def import_students_from_excel(path: str, department_id: Optional[int] = None) -> int:
    """
    Öğrencileri Excel'den yükler ve enrollments ilişkilerini kurar.
    Beklenen sütunlar: number | fullname | class | course_code
    """
    try:
        df = pd.read_excel(path)
    except Exception as e:
        raise ValueError(f"Excel okunamadı: {e}")

    df = _clean_excel_data(df)

    if len(df.columns) >= 4:
        df.columns = ["number", "fullname", "class", "course_code"]
    else:
        raise ValueError("Excel sütunları eksik. Beklenen: number | fullname | class | course_code")

    df = df.dropna(subset=["number", "fullname"])
    df["number"] = df["number"].astype(str).str.strip()
    df = df[df["number"] != ""]

    unique_students = df[["number", "fullname", "class"]].drop_duplicates(subset=["number"])

    dept_id = department_id if department_id is not None else get_department_id("Bilgisayar Muhendisligi")
    students_added = 0
    enrollments_added = 0

    for _, row in unique_students.iterrows():
        number = str(row["number"]).strip()
        name = str(row["fullname"]).strip()
        class_name = str(row.get("class", "")).strip()

        existing = fetch_all("SELECT id FROM students WHERE department_id=%s AND number=%s", [dept_id, number])
        if not existing:
            grade = 1
            for n in (5,4,3,2,1):
                if str(n) in class_name:
                    grade = n
                    break

            execute("""
                INSERT INTO students (department_id, number, fullname, grade)
                VALUES (%s, %s, %s, %s)
            """, [dept_id, number, name, grade])
            students_added += 1

    for _, row in df.iterrows():
        number = str(row["number"]).strip()
        course_code = str(row.get("course_code", "")).strip()
        if not number or not course_code:
            continue

        s = fetch_all("SELECT id FROM students WHERE department_id=%s AND number=%s", [dept_id, number])
        c = fetch_all("SELECT id FROM courses WHERE department_id=%s AND code=%s", [dept_id, course_code])
        if not s or not c:
            continue

        sid, cid = s[0]["id"], c[0]["id"]
        exists = fetch_all(
            "SELECT id FROM enrollments WHERE student_id = %s AND course_id = %s",
            [sid, cid]
        )
        if not exists:
            execute("INSERT INTO enrollments (student_id, course_id) VALUES (%s, %s)", [sid, cid])
            enrollments_added += 1

    return students_added


def import_manual_excel_file(file_path: str, department_id: Optional[int] = None):
    """Tek dosyadan ders import (öğrenci değil)."""
    import_departments()
    course_count = import_courses_from_excel(file_path, department_id=department_id)
    return course_count

def clear_all_imported_data(department_id: Optional[int] = None):
    """
    Excel’den gelen verileri sil.
    department_id verilirse sadece o bölüme ait students/courses/enrollments silinir.
    """
    total = 0
    if department_id is None:
        total += execute("DELETE FROM enrollments")
        total += execute("DELETE FROM students")
        total += execute("DELETE FROM courses")
        return total

    total += execute("""
        DELETE FROM enrollments e
        USING students s
        WHERE e.student_id = s.id AND s.department_id = %s
    """, [department_id])
    total += execute("DELETE FROM students WHERE department_id = %s", [department_id])
    total += execute("DELETE FROM courses  WHERE department_id = %s", [department_id])

    return total

def update_student_enrollments_for_department(department_id: int) -> int:

    students = fetch_all("""
        SELECT id, number, fullname, grade 
        FROM students 
        WHERE department_id = %s
    """, [department_id])
    
    if not students:
        return 0
    
    added_enrollments = 0
    
    for student in students:
        student_id = student['id']
        student_grade = student['grade']
        student_number = student['number']

        available_courses = fetch_all("""
            SELECT id, code, name, grade, is_elective
            FROM courses
            WHERE department_id = %s AND grade = %s
        """, [department_id, student_grade])
        
        if not available_courses:
            continue

        for course in available_courses:
            course_id = course['id']
            course_code = course['code']

            existing = fetch_all("""
                SELECT id FROM enrollments
                WHERE student_id = %s AND course_id = %s
            """, [student_id, course_id])
            
            if not existing:
                try:
                    try:
                        execute("""
                            INSERT INTO enrollments (student_id, course_id, semester, academic_year, status)
                            VALUES (%s, %s, 'GUZ', '2024-2025', 'ACTIVE')
                        """, [student_id, course_id])
                    except Exception:
                        execute("""
                            INSERT INTO enrollments (student_id, course_id, semester, academic_year)
                            VALUES (%s, %s, 'GUZ', '2024-2025')
                        """, [student_id, course_id])
                    
                    added_enrollments += 1
                    pass
                except Exception as e:
                    pass
    return added_enrollments
