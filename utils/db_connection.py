import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, '.env'))

DATABASE_URL = os.getenv('DATABASE_URL')

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def execute_query(query, params=None):
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SET search_path TO SIZOPI")
                cursor.execute(query, params)
                if cursor.description:  
                    return [dict(row) for row in cursor.fetchall()]
                return None
    except Exception as e:
        print(f"Database error: {e}")
        return None

def execute_transaction(queries, params_list):
    conn = None
    try:
        conn = get_connection()
        conn.autocommit = False
        with conn.cursor() as cursor:
            cursor.execute("SET search_path TO SIZOPI")
            for i, query in enumerate(queries):
                cursor.execute(query, params_list[i])
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Transaction error: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False