from flask import Flask
from utils.datastation import buy_airtime_topup

app = Flask(__name__)
# Load config manually
app.config["DATASTATION_TOKEN"] = "66f2e5c39ac8640f13cd888f161385b12f7e5e92"
app.config["DATASTATION_BASE_URL"] = "https://datastation.com.ng"

payload = {
    "network": "1",
    "amount": "100",
    "mobile_number": "08012345678",
    "Ported_number": True,
    "airtime_type": "VTU"
}

with app.app_context():
    print("Checking Airtime Topup with new token (Dummy Payload)...")
    status, body = buy_airtime_topup(payload)
    print(f"Status: {status}")
    print(f"Body: {body}")
