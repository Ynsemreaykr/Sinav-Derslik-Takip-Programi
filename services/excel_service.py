# services/excel_service.py
import pandas as pd
from typing import Optional
from services.db import fetch_all, execute

# =============== Yardımcı Fonksiyonlar ===============

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
            print(f"Departman eklendi: {name}")
        else:
            print(f"Departman zaten mevcut: {name}")

def get_department_id(department_name: str) -> int:
    result = fetch_all("SELECT id FROM departments WHERE name = %s", [department_name])
    if result:
        return result[0]['id']
    # En az bir departman olmalı; seed edilmediyse fallback:
    return 1

# =============== Ders ===============

def _normalize_turkish(text: str) -> str:
    """Türkçe karakterleri normalize et (ı->i, ş->s, İ->i, Ş->s vb.)"""
    # Önce Türkçe büyük harfleri küçük harfe çevir
    replacements = {
        'İ': 'i', 'I': 'i',  # Türkçe İ ve İngilizce I
        'Ş': 's', 'Ğ': 'g', 'Ü': 'u', 
        'Ö': 'o', 'Ç': 'c',
        'ı': 'i', 'ş': 's', 'ğ': 'g', 
        'ü': 'u', 'ö': 'o', 'ç': 'c'
    }
    for tr_char, en_char in replacements.items():
        text = text.replace(tr_char, en_char)
    # Sonra normal küçük harfe çevir
    return text.lower()

def import_courses_from_excel(path: str, department_id: Optional[int] = None) -> int:
    """
    Ders listesini Excel'den yükler.
    Beklenen sütunlar (ilk satır başlık olabilir): code | name | instructor
    """
    try:
        df = pd.read_excel(path, header=None)
    except Exception as e:
        raise ValueError(f"Excel okunamadı: {e}")

    # Ders listesi için _clean_excel_data kullanma, çünkü başlıkları kaybediyoruz
    # df = _clean_excel_data(df)
    
    # Boş satırları temizle (ama başlık satırlarını korumak için sadece tamamen boş olanları sil)
    # df = df.dropna(how="all")  # Bu başlıkları da siliyor!

    if len(df.columns) >= 3:
        df.columns = ["code", "name", "instructor"]
    else:
        raise ValueError("Excel sütunları eksik. En az 3 sütun bekleniyor: code | name | instructor")

    # Boş değerleri doldur
    df = df.fillna("")
    df["code"] = df["code"].astype(str).str.strip()
    df["name"] = df["name"].astype(str).str.strip()
    df["instructor"] = df["instructor"].astype(str).str.strip()

    added = 0
    dept_id = department_id if department_id is not None else get_department_id("Bilgisayar Muhendisligi")
    
    # Başlangıç değerleri
    current_grade = 1
    current_is_elective = False

    for idx, row in df.iterrows():
        code = str(row["code"]).strip()
        name = str(row["name"]).strip()
        instructor = str(row.get("instructor", "")).strip()

        # Başlık satırı mı kontrol et
        normalized = _normalize_turkish(code)
        
        # "SEÇMELİ DERS" veya "SEÇİMLİK DERS" kontrolü
        if "secmeli" in normalized or "secimlik" in normalized:
            current_is_elective = True
            print(f"{current_grade}. Sinif (Secmeli) basligi bulundu")
            continue
        
        # Sınıf başlığı kontrolü (1. Sınıf, 2. Sınıf, vb.)
        for n in range(1, 6):
            if f"{n}." in normalized and "sinif" in normalized:
                current_grade = n
                current_is_elective = False
                print(f"{n}. Sinif (Zorunlu) basligi bulundu")
                break
        
        # Geçersiz satırları atla
        if not code or code.upper() in ("DERS KODU", "CODE", "DERS"):
            continue
        
        # Sınıf başlığı satırını atla
        if "sinif" in normalized:
            continue

        existing = fetch_all("SELECT id FROM courses WHERE department_id=%s AND code=%s", [dept_id, code])
        if not existing:
            execute("""
                INSERT INTO courses (department_id, code, name, instructor, grade, is_elective)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [dept_id, code, name, instructor, current_grade, current_is_elective])
            added += 1

    print(f"{added} ders eklendi (dept_id={dept_id}).")
    return added

# =============== Öğrenci ===============

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

    # Öğrenciler
    for _, row in unique_students.iterrows():
        number = str(row["number"]).strip()
        name = str(row["fullname"]).strip()
        class_name = str(row.get("class", "")).strip()

        existing = fetch_all("SELECT id FROM students WHERE department_id=%s AND number=%s", [dept_id, number])
        if not existing:
            # sınıftan grade çıkar (1..5 arası)
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

    print(f"{students_added} ogrenci eklendi (dept_id={dept_id}).")

    # Enrollments
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

    print(f"{enrollments_added} ogrenci-ders iliskisi eklendi.")
    return students_added

# =============== Genel Import & Cleanup ===============

def import_manual_excel_file(file_path: str, department_id: Optional[int] = None):
    """Tek dosyadan ders import (öğrenci değil)."""
    print(f"Excel dosyasi yukleniyor: {file_path}")
    import_departments()
    course_count = import_courses_from_excel(file_path, department_id=department_id)
    print(f"{course_count} ders import edildi.")
    return course_count

def clear_all_imported_data(department_id: Optional[int] = None):
    """
    Excel’den gelen verileri sil.
    department_id verilirse sadece o bölüme ait students/courses/enrollments silinir.
    """
    total = 0
    if department_id is None:
        # Tüm bölümler (FK sırası önemli)
        total += execute("DELETE FROM enrollments")
        total += execute("DELETE FROM students")
        total += execute("DELETE FROM courses")
        print(f"Tum bolumlerde veri temizlendi. Toplam silinen: {total}")
        return total

    # Sadece bir departman için temizle
    total += execute("""
        DELETE FROM enrollments e
        USING students s
        WHERE e.student_id = s.id AND s.department_id = %s
    """, [department_id])
    total += execute("DELETE FROM students WHERE department_id = %s", [department_id])
    total += execute("DELETE FROM courses  WHERE department_id = %s", [department_id])

    print(f"dept_id={department_id} icin veri temizlendi. Toplam silinen: {total}")
    return total
