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

# def execute_query(sql_query, params=None):
#     with get_db_connection() as conn:
#         with conn.cursor() as cursor:
#             cursor.execute(sql_query, params or [])
#             return cursor.fetchall()
    
# def execute_transaction(sql_query, params=None):
#     try:
#         with get_db_connection() as conn:
#             with conn.cursor() as cursor:
#                 print(f"Executing query: {sql_query}")  
#                 print(f"With parameters: {params}")     
#                 cursor.execute(sql_query, params or [])
#                 conn.commit()
#                 print("Transaction committed successfully") 
#                 return True
#     except Exception as e:
#         print(f"Error in execute_transaction: {str(e)}")  
#         return False


def execute_query(sql: str, params: tuple | list | None = None) -> list[dict]:
    """
    Jalankan SELECT (atau query yang mengembalikan baris) dan kembalikan list of dict.
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        columns = [col[0] for col in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
    return [dict(zip(columns, row)) for row in rows]

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
