import requests
import json
import uuid

BASE_URL = "http://127.0.0.1:5000/api"

def login(email, password):
    url = f"{BASE_URL}/auth/login"
    payload = {"email": email, "password": password}
    try:
        response = requests.post(url, json=payload)
        response.json() # ensure valid json
        if response.status_code != 200:
             print(f"Login failed: {response.text}")
             return None
        return response.json()['data']['token']
    except Exception as e:
        print(f"Login error: {e}")
        return None

def test_admin_access():
    print("--- Testing Admin Access ---")
    
    # Login as Admin
    # Assuming 'admin.majire@data.com' / '12345678' from seed_admin.py
    print("Logging in as admin...")
    token = login("admin.majire@data.com", "12345678")
    
    if not token:
        print("❌ Admin login failed. Cannot proceed.")
        return

    print("✅ Admin logged in.")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. List Users
    print("\nFetching Users...")
    res = requests.get(f"{BASE_URL}/admin/users", headers=headers)
    if res.status_code == 200:
        data = res.json()['data']
        users = data['users']
        print(f"✅ Users fetched successfully. Count: {len(users)}")
        if len(users) > 0:
            print(f"Sample User: {users[0]['email']} (Admin: {users[0]['is_admin']})")
    else:
        print(f"❌ Failed to fetch users: {res.status_code} - {res.text}")

    # 2. List Transactions
    print("\nFetching Transactions...")
    res = requests.get(f"{BASE_URL}/admin/transactions", headers=headers)
    if res.status_code == 200:
        data = res.json()['data']
        txs = data['transactions']
        print(f"✅ Transactions fetched successfully. Count: {len(txs)}")
        if len(txs) > 0:
            print(f"Sample Tx: {txs[0]['reference']} - {txs[0]['amount']}")
    else:
        print(f"❌ Failed to fetch transactions: {res.status_code} - {res.text}")

if __name__ == "__main__":
    test_admin_access()
