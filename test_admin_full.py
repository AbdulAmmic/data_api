import requests
import json
import uuid

BASE_URL = "http://127.0.0.1:5000/api"

def login(email, password):
    url = f"{BASE_URL}/auth/login"
    payload = {"email": email, "password": password}
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
             print(f"Login failed: {response.text}")
             return None
        return response.json()['data']['token']
    except Exception as e:
        print(f"Login error: {e}")
        return None

def test_admin_full():
    print("--- Testing FULL Admin Dashboard API ---")
    
    # Login
    print("Logging in as admin...")
    token = login("admin.majire@data.com", "12345678")
    if not token: return

    headers = {"Authorization": f"Bearer {token}"}

    # 1. Stats
    print("\n1. Testing Stats...")
    res = requests.get(f"{BASE_URL}/admin/stats", headers=headers)
    if res.status_code == 200:
        print(f"✅ Stats: {res.json()['data']}")
    else:
        print(f"❌ Stats Failed: {res.text}")

    # 2. Users (Wallets)
    print("\n2. Testing Users...")
    res = requests.get(f"{BASE_URL}/admin/users", headers=headers)
    if res.status_code == 200:
        users = res.json()['data']['users']
        print(f"✅ Users: Found {len(users)}")
        if users: print(f"   Sample: {users[0]['email']} - Bal: {users[0]['balance']}")
    else:
        print(f"❌ Users Failed: {res.text}")

    # 3. Transactions
    print("\n3. Testing Transactions...")
    res = requests.get(f"{BASE_URL}/admin/transactions", headers=headers)
    if res.status_code == 200:
        txs = res.json()['data']['transactions']
        print(f"✅ Transactions: Found {len(txs)}")
        if txs: print(f"   Sample: {txs[0]['reference']} - Amt: {txs[0]['amount']}")
    else:
        print(f"❌ Transactions Failed: {res.text}")

    # 4. Complaints
    print("\n4. Testing Complaints...")
    res = requests.get(f"{BASE_URL}/admin/complaints", headers=headers)
    if res.status_code == 200:
        data = res.json()['data']
        # Handle pagination structure if different
        complaints = data.get('complaints', [])
        print(f"✅ Complaints: Found {len(complaints)}")
    else:
        print(f"❌ Complaints Failed: {res.text}")

if __name__ == "__main__":
    test_admin_full()
