# database/table_manager.py
import os
from typing import Tuple
from database.connection import get_conn_cursor

SQL_FILE_PATH = os.path.join(os.path.dirname(__file__), "createtable.sql")

TABLES_IN_ORDER = [
    "departments",
    "users",
    "classrooms",
    "courses",
    "students",
    "student_courses",
    "enrollments",
    "exam_schedules",
    "exams",
    "exam_classrooms",
    "seating_plans"
]

def table_exists(table_name: str) -> bool:
    """Tablonun var olup olmadığını kontrol eder."""
    try:
        with get_conn_cursor() as (_, cur):
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, [table_name])
            result = cur.fetchone()
            return result['exists'] if result else False
    except Exception as e:
        return False

def read_sql_file() -> str:
    """createtable.sql dosyasını okur."""
    if not os.path.exists(SQL_FILE_PATH):
        raise FileNotFoundError(f"SQL dosyasi bulunamadi: {SQL_FILE_PATH}")
    
    with open(SQL_FILE_PATH, 'r', encoding='utf-8') as f:
        return f.read()

def extract_table_creation_sql(sql_content: str, table_name: str) -> str:
    """SQL içeriğinden belirli tablo için CREATE TABLE çıkarır."""
    lines = sql_content.split('\n')
    table_sql = []
    capturing = False
    
    for line in lines:
        if f"CREATE TABLE IF NOT EXISTS {table_name}" in line:
            capturing = True
            table_sql.append(line)
            continue
        
        if capturing:
            table_sql.append(line)
            if line.strip().endswith(');'):
                break
    
    return '\n'.join(table_sql) if table_sql else ""

def create_table(table_name: str, sql_content: str) -> bool:
    """Tabloyu oluşturur."""
    try:
        create_sql = extract_table_creation_sql(sql_content, table_name)
        
        if not create_sql:
            return False
        
        with get_conn_cursor(autocommit=True) as (_, cur):
            cur.execute(create_sql)
            return True
            
    except Exception as e:
        return False

def create_indexes_and_triggers(sql_content: str) -> None:
    """İndeksleri ve trigger'ları oluşturur."""
    try:
        lines = sql_content.split('\n')
        
        with get_conn_cursor(autocommit=True) as (_, cur):
            for line in lines:
                if line.strip().startswith("CREATE INDEX IF NOT EXISTS"):
                    try:
                        cur.execute(line.strip())
                    except Exception:
                        pass
        
        
        with get_conn_cursor(autocommit=True) as (_, cur):
            trigger_func = """
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            """
            cur.execute(trigger_func)
        
        pass
        
    except Exception as e:
        pass

def check_and_create_all_tables() -> Tuple[int, int]:
    """Tüm tabloları kontrol eder ve oluşturur."""
    try:
        sql_content = read_sql_file()
    except FileNotFoundError as e:
        return 0, 0
    
    existing_count = 0
    created_count = 0
    
    for table_name in TABLES_IN_ORDER:
        if table_exists(table_name):
            existing_count += 1
        else:
            if create_table(table_name, sql_content):
                created_count += 1
    
    create_indexes_and_triggers(sql_content)
    
    return existing_count, created_count

def verify_all_tables() -> bool:
    """Tüm tabloların var olduğunu doğrular."""
    missing = []
    
    for table_name in TABLES_IN_ORDER:
        if not table_exists(table_name):
            missing.append(table_name)
    
    if missing:
        return False
    
    return True

