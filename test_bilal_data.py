import requests
token = "63c91fcc529ea3f403e773c5fd7d6562c892c74293f1ac7b1c1931cfd8b8"
url = "https://bilalsadasub.com/api/data"
headers = {
    "Authorization": f"Token {token}",
    "Content-Type": "application/json"
}
try:
    r = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Body: {r.text}")
except Exception as e:
    print(f"Error: {e}")
