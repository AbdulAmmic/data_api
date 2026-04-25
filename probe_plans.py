import requests
url = "https://bilalsadasub.com/api/data"
headers = {"Authorization": "Token ef993044f4599b78b841ea23764f4303361bf967"}
r = requests.get(url, headers=headers)
print(f"Status: {r.status_code}")
print(f"Body: {r.text[:2000]}")
