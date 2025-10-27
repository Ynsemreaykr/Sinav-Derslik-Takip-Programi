# services/auth_service.py
from database.db import fetch_one, execute
from utils.helpers import hash_password
from models.user import User

def authenticate_user(email: str, password: str) -> User | None:
    """E-posta ve şifre ile giriş doğrulaması"""
    user_row = fetch_one("SELECT * FROM users WHERE email = %s", [email])
    if not user_row:
        return None

    hashed = hash_password(password)
    if user_row["password_hash"] != hashed:
        return None

    return User.from_row(user_row)

def ensure_default_admin():
    """Veritabanında admin yoksa otomatik olarak oluşturur"""
    admin = fetch_one("SELECT id FROM users WHERE role = 'ADMIN'")
    if admin:
        return  # zaten var

    email = "admin@university.edu"
    password = "admin123"
    password_hash = hash_password(password)

    execute("""
        INSERT INTO users (email, password_hash, role, department_id)
        VALUES (%s, %s, 'ADMIN', NULL)
    """, [email, password_hash])


def create_coordinator(email: str, password: str, department_id: int) -> tuple[bool, str]:

    existing = fetch_one("SELECT id FROM users WHERE email = %s", [email])
    if existing:
        return False, "Bu e-posta adresi zaten kayitli!"
    
    # Bölümde koordinatör var mı kontrolü
    existing_coord = fetch_one("""
        SELECT id, email FROM users 
        WHERE department_id = %s AND role = 'COORDINATOR'
    """, [department_id])
    
    if existing_coord:
        return False, f"Bu bolumde zaten bir koordinator var!\n\nMevcut: {existing_coord['email']}\n\nOnce mevcut koordinatoru silip yeni koordinator ekleyebilirsiniz."
    
    # Koordinatör oluştur
    password_hash = hash_password(password)
    execute("""
        INSERT INTO users (email, password_hash, role, department_id)
        VALUES (%s, %s, 'COORDINATOR', %s)
    """, [email, password_hash, department_id])
    
    return True, "Koordinator basariyla eklendi!"
