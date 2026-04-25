import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BILALSADASUB_TOKEN") or "ef993044f4599b78b841ea23764f4303361bf967"
# Ensure we don't double prefix
if TOKEN and not TOKEN.startswith("Token "):
    AUTH_HEADER = f"Token {TOKEN}"
else:
    AUTH_HEADER = TOKEN or ""

BASE_URLS = [
    "https://bilalsadasub.com/api"
]

def probe():
    print(f"Using Auth Header: {AUTH_HEADER[:10]}...")
    
    for base in BASE_URLS:
        print(f"\n--- Testing Base: {base} ---")
        headers = {
            "Authorization": AUTH_HEADER,
            "Content-Type": "application/json"
        }
        
        # 1. Check User
        print(" [GET] /user")
        try:
            res = requests.get(f"{base}/user", headers=headers, timeout=10)
            print(f" Status: {res.status_code}")
            if res.status_code == 200:
                print(f" Body: {res.text[:500]}")
            else:
                print(f" Error: {res.text[:200]}")
        except Exception as e:
            print(f" Request Exception: {e}")

        # 2. Check Data
        print(" [GET] /data")
        try:
            res = requests.get(f"{base}/data", headers=headers, timeout=10)
            print(f" Status: {res.status_code}")
            if res.status_code == 200:
                print(f" Body: {res.text[:500]}")
            else:
                 print(f" Error: {res.text[:200]}")
        except Exception as e:
             print(f" Request Exception: {e}")

if __name__ == "__main__":
    probe()
