import requests
import base64
import json

username = "247midata"
password = "Mi@122429"

# Base64 encode the credentials
auth_str = f"{username}:{password}"
encoded_auth = base64.b64encode(auth_str.encode()).decode()

url = "https://bilalsadasub.com/api/user"
headers = {
    "Authorization": f"Basic {encoded_auth}",
    "Content-Type": "application/json"
}

print(f"Requesting token for {username}...")
try:
    # Based on docs, it's a POST request to generate token
    r = requests.post(url, headers=headers, timeout=20)
    print(f"Status: {r.status_code}")
    print(f"Body: {r.text}")
    
    if r.status_code in (200, 201):
        data = r.json()
        if data.get("status") == "success":
            token = data.get("AccessToken")
            print(f"\nSUCCESS! NEW TOKEN: {token}")
        else:
            print(f"\nFailed: {data.get('message')}")
    else:
        print(f"\nError: API returned {r.status_code}")
except Exception as e:
    print(f"Exception: {e}")
