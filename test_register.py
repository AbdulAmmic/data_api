import requests
import json

url = "http://127.0.0.1:5000/api/auth/register"
payload = {
    "full_name": "Test User",
    "email": "test_user_debug_1@example.com",
    "phone": "08012345678",
    "password": "password123"
}
headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    print(response.text)
    try:
        print("JSON Response:", response.json())
    except:
        print("Response is not JSON")
except Exception as e:
    print(f"Error: {e}")
