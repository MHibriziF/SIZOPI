import psycopg2
from django.conf import settings
from django.db import connection, transaction

def get_db_connection():
    try:
        connection = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT'],
            options="-c search_path=SIZOPI"
        )
        return connection
    except psycopg2.Error as e:
        print(f"Database connection failed: {e}")
        raise


def execute_query(sql, params=None):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or [])
            cols = [c[0] for c in cur.description] if cur.description else []
            rows = cur.fetchall()
        return [dict(zip(cols, r)) for r in rows]
    finally:
        conn.close()

def execute_transaction(
    sql_statements: str | list[str],
    params_list: list[tuple] | tuple | None = None
) -> bool:
    """
    Jalankan satu atau banyak statement di dalam satu transaksi.
    - sql_statements: satu string SQL atau list SQL
    - params_list: None, satu tuple, atau list of tuple sesuai jumlah SQL
    """
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                if isinstance(sql_statements, str):
                    cursor.execute(sql_statements, params_list or [])
                else:
                    for idx, sql in enumerate(sql_statements):
                        params = None
                        if isinstance(params_list, (list, tuple)):
                            params = params_list[idx] if isinstance(params_list[0], (list, tuple)) else params_list
                        cursor.execute(sql, params or [])
        return True
    except Exception as e:
        return False
