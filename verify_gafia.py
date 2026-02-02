import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from flask import Flask
from config import Config
from utils.gafiapay import generate_virtual_account

# Setup minimal Flask app context
app = Flask(__name__)
app.config.from_object(Config)

def test_gafiapay():
    print("Testing Gafiapay Integration...")
    
    # Check config
    api_key = app.config.get("GAFIAPAY_API_KEY")
    secret_key = app.config.get("GAFIAPAY_SECRET_KEY")
    
    print(f"API Key present: {bool(api_key)}")
    print(f"Secret Key present: {bool(secret_key)}")
    
    if not api_key or not secret_key:
        print("ERROR: Keys missing in config!")
        return

    with app.app_context():
        # Using a dummy email/name for testing. 
        # Note: This might actually create a virtual account if the API is live!
        # Use a clearly test-designated email.
        name = "Test User"
        email = "antigravity_test@example.com"
        
        print(f"Attempting to generate virtual account for {email}...")
        status, data = generate_virtual_account(name, email)
        
        print(f"Status Code: {status}")
        print(f"Response Data: {data}")
        
        if status in [200, 201] and data.get("status") == "success":
            print("SUCCESS: Virtual Account generation endpoint reachable and authenticated.")
        else:
            print("FAILED or API returned error (could be expected if keys are invalid or test mode restrictions).")

if __name__ == "__main__":
    with open("gafia_test_log.txt", "w") as f:
        sys.stdout = f
        test_gafiapay()
        sys.stdout = sys.__stdout__
    
    # Print content to stdout as well just in case
    with open("gafia_test_log.txt", "r") as f:
        print(f.read())
