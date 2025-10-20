# services/auth_service.py
from database.db import fetch_one, execute
from utils.helpers import hash_password
from models.user import User


# ======================================================
# Kullanıcı doğrulama (login)
# ======================================================
def authenticate_user(email: str, password: str) -> User | None:
    """E-posta ve şifre ile giriş doğrulaması"""
    user_row = fetch_one("SELECT * FROM users WHERE email = %s", [email])
    if not user_row:
        return None

    # Hash kontrolü
    hashed = hash_password(password)
    if user_row["password_hash"] != hashed:
        return None

    return User.from_row(user_row)


# ======================================================
# Varsayılan admin oluşturma (ilk girişte)
# ======================================================
def ensure_default_admin():
    """Veritabanında admin yoksa otomatik olarak oluşturur"""
    admin = fetch_one("SELECT id FROM users WHERE role = 'ADMIN'")
    if admin:
        return  # zaten var

    print("⚙️ Varsayılan admin oluşturuluyor...")
    email = "admin@university.edu"
    password = "admin123"
    password_hash = hash_password(password)

    execute("""
        INSERT INTO users (email, password_hash, role, department_id)
        VALUES (%s, %s, 'ADMIN', NULL)
    """, [email, password_hash])

    print(f"✅ Admin oluşturuldu → {email} / {password}")


# ======================================================
# Bölüm koordinatörü oluşturma (UI'den çağrılır)
# ======================================================
def create_coordinator(email: str, password: str, department_id: int) -> bool:
    """Yeni bölüm koordinatörü ekle"""
    existing = fetch_one("SELECT id FROM users WHERE email = %s", [email])
    if existing:
        return False

    password_hash = hash_password(password)
    execute("""
        INSERT INTO users (email, password_hash, role, department_id)
        VALUES (%s, %s, 'COORDINATOR', %s)
    """, [email, password_hash, department_id])
    return True
