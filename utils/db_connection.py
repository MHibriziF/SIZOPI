import psycopg2
from django.conf import settings

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

def execute_query(sql_query, params=None):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql_query, params or [])
            return cursor.fetchall()
    
def execute_transaction(sql_query, params=None):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                print(f"Executing query: {sql_query}")  
                print(f"With parameters: {params}")     
                cursor.execute(sql_query, params or [])
                conn.commit()
                print("Transaction committed successfully") 
                return True
    except Exception as e:
        print(f"Error in execute_transaction: {str(e)}")  
        return False