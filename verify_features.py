
import requests

BASE_URL = "http://127.0.0.1:5000"

def test_routes():
    try:
        # 1. Check Homepage
        resp = requests.get(f"{BASE_URL}/")
        print(f"Homepage: {resp.status_code}")
        
        # 2. Check Marketplace home for user 1
        resp = requests.get(f"{BASE_URL}/home/1")
        print(f"User Home: {resp.status_code}")
        if "Recommended for You" in resp.text:
            print("Personalization section found!")
        
        # 3. Check Vendor Orders for vendor 4
        resp = requests.get(f"{BASE_URL}/vendorOrders/4")
        print(f"Vendor Orders Page: {resp.status_code}")
        if "Incoming Marketplace Orders" in resp.text:
            print("Vendor Dashboard content found!")
        
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_routes()
