
from market import my_sql, app
from werkzeug.security import generate_password_hash
import sys

def migrate():
    with app.app_context():
        cur = my_sql.connection.cursor()
        
        # 1. Migrate Customers
        cur.execute("SELECT customer_id, password_hash FROM customer")
        customers = cur.fetchall()
        for cid, pw in customers:
            # Simple check to avoid double hashing if we run this twice
            if not pw.startswith('pbkdf2:sha256:'):
                hashed = generate_password_hash(pw)
                cur.execute("UPDATE customer SET password_hash = %s WHERE customer_id = %s", (hashed, cid))
                print(f"Hashed password for customer {cid}")

        # 2. Migrate Vendors
        cur.execute("SELECT vendor_id, password_hash FROM vendor")
        vendors = cur.fetchall()
        for vid, pw in vendors:
            if not pw.startswith('pbkdf2:sha256:'):
                hashed = generate_password_hash(pw)
                cur.execute("UPDATE vendor SET password_hash = %s WHERE vendor_id = %s", (hashed, vid))
                print(f"Hashed password for vendor {vid}")

        my_sql.connection.commit()
        cur.close()
        print("Migration complete!")

if __name__ == "__main__":
    migrate()
