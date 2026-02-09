from flask import Flask
from utils.datastation import get_user_details, buy_airtime_topup
import time

app = Flask(__name__)
# Load config manually
app.config["DATASTATION_TOKEN"] = "9269ea4cbabe84c94ea5bf41db03f09a924f0f47"
app.config["DATASTATION_BASE_URL"] = "https://datastation.com.ng"

with app.app_context():
    with open("verify_result.txt", "w") as f:
        f.write("Checking Airtime Topup with CORRECT token...\n")
        payload = {
            "network": "1", # MTN
            "amount": "50",
            "mobile_number": "08012345678",
            "Ported_number": True,
            "airtime_type": "VTU"
        }
        status, body = buy_airtime_topup(payload)
        f.write(f"Status: {status}\n")
        f.write(f"Body: {body}\n")
    print("Done writing to verify_result.txt")
