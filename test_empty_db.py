
import pymysql

def test_no_password():
    host = '127.0.0.1'
    user = 'root'
    password = ''
    try:
        print(f"Attempting empty password for {user}...")
        conn = pymysql.connect(host=host, user=user, password=password)
        print("Connected with empty password!")
        conn.close()
    except Exception as e:
        print(f"Empty password failed: {e}")

if __name__ == "__main__":
    test_no_password()
