import requests
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BILALSADASUB_TOKEN")
BASE_URL = os.getenv("BILALSADASUB_BASE_URL")

headers = {
    "Authorization": f"Token {TOKEN}",
    "Content-Type": "application/json"
}

url = f"{BASE_URL}/api/user"
print(f"Testing URL: {url}")
print(f"Using Token: {TOKEN[:5]}...")

try:
    res = requests.get(url, headers=headers, timeout=10)
    print(f"Status Code: {res.status_code}")
    print(f"Response Body: {res.text}")
except Exception as e:
    print(f"Error: {e}")
