
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DATASTATION_TOKEN")
HEADERS = {"Authorization": TOKEN, "Content-Type": "application/json"}

URLS = [
    "https://datastationapi.com/api/user/",
    "https://datastation.com.ng/api/user/"
]

print(f"Testing Token: {TOKEN[:10]}...")

for url in URLS:
    try:
        print(f"Checking {url} ...")
        res = requests.get(url, headers=HEADERS, timeout=10)
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            print("SUCCESS: Valid Token and URL")
            print(res.text[:100])
            break
        else:
            print(f"FAILED: {res.status_code}")
            print(res.text[:100])
    except Exception as e:
        print(f"Error: {e}")
