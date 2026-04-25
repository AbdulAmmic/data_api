import requests
import base64

username = "247midata"
password = "WRONG_PASSWORD"

auth_str = f"{username}:{password}"
encoded_auth = base64.b64encode(auth_str.encode()).decode()

url = "https://bilalsadasub.com/api/user"
headers = {
    "Authorization": f"Basic {encoded_auth}",
    "Content-Type": "application/json"
}

r = requests.post(url, headers=headers, timeout=10)
print(f"Status: {r.status_code}")
print(f"Body: {r.text}")
