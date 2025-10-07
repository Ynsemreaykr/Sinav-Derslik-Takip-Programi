# database/connection.py
import os
from contextlib import contextmanager
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

POOL: SimpleConnectionPool | None = None

def init_pool(minconn: int = 1, maxconn: int = 5):
    global POOL
    if POOL is None:
        import psycopg2
        POOL = SimpleConnectionPool(
            minconn, maxconn,
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            dbname=os.getenv("DB_NAME", "obs"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "1234")
        )

@contextmanager
def get_conn_cursor(dict_rows: bool = True, autocommit: bool = False):
    """
    with get_conn_cursor() as (conn, cur):
        cur.execute("SELECT 1")
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
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        POOL.putconn(conn)
