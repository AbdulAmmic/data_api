
import requests
import json

# Configuration
BASE_URL = "http://localhost:5000"
WEBHOOK_URL = f"{BASE_URL}/webhooks/gafiapay"

# 1. First, ensure we have a user and account to test with.
# We'll use the 'register' endpoint to create one if needed, or just assume one exists if we seeded.
# For this test, let's try to hit the webhook with a random account number and see if it fails gracefully,
# OR we can try to register a user first.

def register_user():
    print("Registering test user...")
    resp = requests.post(f"{BASE_URL}/api/auth/register", json={
        "full_name": "Webhook Tester",
        "email": "webhook@test.com",
        "phone": "08011112222",
        "password": "password123"
    })
    if resp.status_code in [200, 201]:
        data = resp.json().get("data", {})
        user = data.get("user", {})
        print(f"User created: {user.get('email')}")
        return user
    elif resp.status_code == 409:
        print("User already exists.")
        return {"email": "webhook@test.com"} # minimal
    else:
        print(f"Registration failed: {resp.text}")
        return None

# We need to manually inject a dedicated account for this user because the real API calls Gafiapay
# which might fail locally. 
# So we will access the DB directly? No, we shouldn't.
# We will trust that if the user exists, we can try to send a webhook.
# But wait, the webhook looks up `UserDedicatedAccount`.
# We need to Insert a fake UserDedicatedAccount into the local DB for testing.

# Since we can't easily run SQL from here without the app context, 
# let's assume the user has a way to test this or we rely on the log output.

# Payload based on the code's expectation:
# { "event": "transaction.successful", "data": { "reference": "...", "amount": 100, "virtual_account_number": "..." } }

payload = {
  "event": "payment.received",
  "data": {
    "transaction": {
      "id": "6981eb8288cabd6b541cb2eb",
      "orderNo": "MI2018664518015655936",
      "amount": 300,
      "metadata": {
        "virtualAccountNo": "9988776655" # Matches our fake seed
      }
    }
  }
}

print(f"Sending Webhook to {WEBHOOK_URL}...")
try:
    resp = requests.post(WEBHOOK_URL, json=payload)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Request failed: {e}")
