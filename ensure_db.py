
import pymysql
import yaml

def setup_db():
    try:
        with open('database.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        host = config.get('mysql_host', '127.0.0.1')
        user = config.get('mysql_user', 'root')
        password = config.get('mysql_password', '')
        db_name = config.get('mysql_db', 'comp7640_marketplace')

        print(f"Connecting to MySQL at {host}...")
        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            charset='utf8mb4'
        )
        
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            print(f"Database '{db_name}' ensured.")
        
        conn.select_db(db_name)
        
        # Check if tables exist
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            if not tables:
                print("No tables found. Importing schema...")
                # We need to run the SQL files. 
                # Since we are using pymysql, we might need to parse the SQL or use mysql command.
                # Let's try to find mysql.exe first.
            else:
                print(f"Found {len(tables)} tables.")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    setup_db()
