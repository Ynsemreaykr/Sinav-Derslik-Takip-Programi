# database/init_db.py
from database.connection import get_conn_cursor, init_pool

def test_connection():
    init_pool()
    print("🔗 Bağlantı havuzu oluşturuldu.")
    with get_conn_cursor() as (_, cur):
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print("✅ PostgreSQL bağlantısı başarılı!")
        print("Veritabanı sürümü:", version['version'])

def main():
    test_connection()

if __name__ == "__main__":
    main()
