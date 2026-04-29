"""
Test Bilalsadasub airtime API with correct auth methods.
- GET /api/user uses Basic auth
- POST /api/topup uses Token auth

Usage: python test_airtime.py
"""
import requests
import base64
import sys
import os
import json

# ---- Load env ----
TOKEN = None
BASE_URL = "https://bilalsadasub.com"
USERNAME = None
PASSWORD = None

env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("BILALSADASUB_TOKEN="):
                TOKEN = line.split("=", 1)[1].strip()
            if line.startswith("BILALSADASUB_BASE_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")

# Credentials from generate_bilal_token.py
USERNAME = "247midata"
PASSWORD = "Mi@122429"

if not TOKEN:
    print("[FAIL] BILALSADASUB_TOKEN not found in .env")
    sys.exit(1)

token_headers = {
    "Authorization": f"Token {TOKEN}",
    "Content-Type": "application/json",
}

auth_str = f"{USERNAME}:{PASSWORD}"
encoded_auth = base64.b64encode(auth_str.encode()).decode()
basic_headers = {
    "Authorization": f"Basic {encoded_auth}",
    "Content-Type": "application/json",
}

print(f"[OK] Token: {TOKEN[:16]}...")
print(f"[OK] Base URL: {BASE_URL}")

# ---- Step 1: Check balance using Basic auth (as docs show) ----
print("\n--- Step 1: Check Balance (POST /api/user with Basic auth) ---")
r = requests.post(f"{BASE_URL}/api/user", headers=basic_headers, timeout=15)
print(f"Status: {r.status_code}")
try:
    data = r.json()
    if data.get("status") == "success":
        balance = data.get("balance", "N/A")
        fresh_token = data.get("AccessToken", TOKEN)
        print(f"[OK] Balance: NGN {balance}")
        print(f"[OK] Token confirmed: {fresh_token[:16]}...")
        # Update token if different
        if fresh_token != TOKEN:
            print(f"[NOTE] Token changed! Updating TOKEN variable.")
            TOKEN = fresh_token
            token_headers["Authorization"] = f"Token {TOKEN}"
    else:
        print(f"[FAIL] Balance check failed: {data}")
        sys.exit(1)
except Exception as e:
    print(f"[FAIL] JSON parse error: {e}\nRaw: {r.text[:300]}")
    sys.exit(1)

# ---- Step 2: Validate topup endpoint is reachable (Token auth) ----
print("\n--- Step 2: Test Airtime Topup Payload (Token auth, REAL call) ---")
print("WARNING: This will send NGN 50 airtime to 07013397088 (test number from docs).")
answer = input("Send test airtime to 07013397088? (yes/no): ").strip().lower()

if answer != "yes":
    print("[SKIP] Skipping live call. Payload structure:")
    payload = {
        "network": 1,
        "amount": 50,
        "phone": "07013397088",
        "plan_type": "VTU",
        "bypass": False,
        "request-id": "TEST_AIRTIME_12345"
    }
    print(json.dumps(payload, indent=2))
    print("\n[OK] Dry run complete. Fix applied:")
    print("  - bypass: False added to payload")
    print("  - Status field in JSON response now checked (not just HTTP status code)")
    sys.exit(0)

payload = {
    "network": 1,          # MTN
    "amount": 50,          # NGN 50
    "phone": "07013397088",
    "plan_type": "VTU",
    "bypass": False,
    "request-id": "TEST_AIRTIME_LIVE_001"
}

r = requests.post(f"{BASE_URL}/api/topup", json=payload, headers=token_headers, timeout=30)
print(f"Status: {r.status_code}")
try:
    result = r.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    if result.get("status") == "success":
        print("\n[OK] Airtime topup SUCCESSFUL!")
    else:
        print(f"\n[FAIL] Topup failed: {result.get('message') or result}")
except Exception as e:
    print(f"[FAIL] JSON parse error: {e}\nRaw: {r.text[:500]}")
