import requests
import base64
auth_str = "247midata:Mi@122429"
encoded = base64.b64encode(auth_str.encode()).decode()
url = "https://bilalsadasub.com/api/user"
headers = {"Authorization": f"Basic {encoded}", "Content-Type": "application/json"}
r = requests.post(url, headers=headers, timeout=10)
print(r.text)
