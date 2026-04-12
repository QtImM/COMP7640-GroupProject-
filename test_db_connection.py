
import yaml
import pymysql
import sys

def test_connection():
    try:
        with open('database.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        host = config.get('mysql_host', '127.0.0.1')
        user = config.get('mysql_user', 'root')
        password = config.get('mysql_password', '')
        db = config.get('mysql_db', 'comp7640_marketplace')

        print(f"Attempting to connect to {host} as {user}...")
        
        # First try to connect to the server without the DB to see if credentials are correct
        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            charset='utf8mb4'
        )
        print("Successfully connected to MySQL server!")
        
        # Now check if the database exists
        try:
            conn.select_db(db)
            print(f"Database '{db}' exists.")
        except Exception as e:
            print(f"Connected to server, but database '{db}' was not found. Details: {e}")
            
        conn.close()
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
