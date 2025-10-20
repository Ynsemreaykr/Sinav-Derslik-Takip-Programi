# database/connection.py
import os
from contextlib import contextmanager
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# =====================================
# .env dosyasını yükle (zorunlu)
# =====================================
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if not os.path.exists(env_path):
    raise FileNotFoundError(".env dosyasi bulunamadi! Lutfen proje kokune ekleyin.")
load_dotenv(env_path)

# Gerekli environment değişkenlerini al (hiçbiri opsiyonel değil)
required_vars = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
missing = [v for v in required_vars if not os.getenv(v)]
if missing:
    raise EnvironmentError(f"Eksik ortam degisken(ler)i: {', '.join(missing)}")

# =====================================
# Bağlantı havuzu (singleton)
# =====================================
POOL: SimpleConnectionPool | None = None

def init_pool(minconn: int = 1, maxconn: int = 5):
    """PostgreSQL bağlantı havuzunu başlatır (.env zorunlu)."""
    global POOL
    if POOL is not None:
        return  # zaten kuruldu

    import psycopg2
    try:
        POOL = SimpleConnectionPool(
            minconn,
            maxconn,
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
        )
        print(f"PostgreSQL baglanti havuzu kuruldu -> {os.getenv('DB_NAME')}@{os.getenv('DB_HOST')}")
    except Exception as e:
        print(f"Baglanti hatasi: {e}")
        raise

# =====================================
# Context manager: connection + cursor
# =====================================
@contextmanager
def get_conn_cursor(dict_rows: bool = True, autocommit: bool = False):
    """
    Veritabanı bağlantısı ve cursor context manager'ı.
    Kullanım:
        with get_conn_cursor() as (_, cur):
            cur.execute("SELECT 1;")
    """
    if POOL is None:
        init_pool()

    conn = POOL.getconn()
    try:
        conn.autocommit = autocommit
        cur = conn.cursor(cursor_factory=RealDictCursor if dict_rows else None)
        yield conn, cur
        if not autocommit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"SQL hata: {e}")
        raise
    finally:
        cur.close()
        POOL.putconn(conn)
