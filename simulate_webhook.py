import requests
import json
import random
import string
import sys

# Configuration
BASE_URL = "http://127.0.0.1:5000"
WEBHOOK_URL = f"{BASE_URL}/api/webhooks/gafiapay"

def generate_ref():
    return "GAFIA-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=12))

def simulate_payment(account_number, amount_naira):
    payload = {
        "event": "transaction.successful",
        "data": {
            "reference": generate_ref(),
            "amount": amount_naira,
            "currency": "NGN",
            "virtual_account_number": account_number,
            "customer": {
                "name": "Simulated Customer",
                "email": "customer@example.com"
            },
            "narration": "Transfer from Checking"
        }
    }

    print(f"Sending Webhook to {WEBHOOK_URL}...")
    print(json.dumps(payload, indent=2))

    try:
        res = requests.post(WEBHOOK_URL, json=payload)
        print(f"\nStatus Code: {res.status_code}")
        try:
            print("Response:", json.dumps(res.json(), indent=2))
        except:
            print("Response Text:", res.text)
            
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the server. Is 'python app.py' running?")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python simulate_webhook.py <account_number> <amount>")
        print("\nExample: python simulate_webhook.py 1234567890 5000")
        
        # Try to find a user's account number to hint the user
        try:
            from app import app
            from models import UserDedicatedAccount, User
            with app.app_context():
                dva = UserDedicatedAccount.query.join(User).filter(User.email.like("%@%")).first()
                if dva:
                    print(f"\nHint: Found existing account number {dva.account_number} for user {dva.user.email}")
                    print(f"Try: python simulate_webhook.py {dva.account_number} 1000")
        except:
            pass
            
    else:
        simulate_payment(sys.argv[1], sys.argv[2])
