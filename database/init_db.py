# database/init_db.py
from services.db import fetch_all, execute
from utils.helpers import hash_password
from database.table_manager import check_and_create_all_tables, verify_all_tables

DEPARTMENTS = [
    "Bilgisayar Muhendisligi",
    "Yazilim Muhendisligi",
    "Elektrik Muhendisligi",
    "Elektronik Muhendisligi",
    "Insaat Muhendisligi",
]

def seed_departments() -> None:
    """Zorunlu 5 bolumu yoksa ekler (idempotent)."""
    for name in DEPARTMENTS:
        existing = fetch_all("SELECT id FROM departments WHERE name = %s", [name])
        if not existing:
            execute("INSERT INTO departments (name) VALUES (%s)", [name])

def create_default_admin() -> None:
    """
    Varsayilan admin yoksa olusturur.
    Email: admin@university.edu  Sifre: admin123
    Idempotent calisir.
    """
    existing = fetch_all("SELECT id FROM users WHERE email = %s", ["admin@university.edu"])
    if existing:
        return

    password_hash = hash_password("admin123")
    execute(
        """
        INSERT INTO users (email, password_hash, role, department_id)
        VALUES (%s, %s, %s, %s)
        """,
        ["admin@university.edu", password_hash, "ADMIN", None],
    )

def initialize_core() -> None:
    """
    GUI açılışında çağrılacak çekirdek başlatma fonksiyonu.
    
    1. Tüm tabloları kontrol eder ve eksikleri oluşturur (createtable.sql'den)
    2. Bölümleri tohunlar
    3. Varsayılan admin kullanıcısını oluşturur
    """
    check_and_create_all_tables()

    if not verify_all_tables():
        raise Exception("Kritik tablolar eksik! Lutfen createtable.sql dosyasini kontrol edin.")

    seed_departments()

    create_default_admin()
