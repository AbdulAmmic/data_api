import requests
token = "63c91fcc529ea3f403e773c5fd7d6562c892c74293f1ac7b1c1931cfd8b8"
url = "https://bilalsadasub.com/api/user"
# headers = {"Authorization": f"Token {token}"}
# Try with just Token prefix
headers = {
    "Authorization": f"Token {token}",
    "Content-Type": "application/json"
}
# Try GET logic (User details usually GET?)
# Doc says: 'The Basic Authentication Is Use To Generate (TOKEN)... 19: Enpoint URL 21: .../api/user'
# But wait, to USE the token? 
# Doc doesn't explicitly show GET /api/user with Token.
# Let's try buy_data (POST) with this token.

payload = {
    "network": 1,
    "phone": "08145463904",
    "data_plan": 11, # Random plan ID
    "bypass": False,
    "request-id": "test_auth_check"
}
r = requests.post("https://bilalsadasub.com/api/data", json=payload, headers=headers)
print(f"POST Status: {r.status_code}")
print(f"POST Body: {r.text}")
