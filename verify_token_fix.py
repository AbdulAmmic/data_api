from flask import Flask
from utils.datastation import get_user_details
from config import Config

app = Flask(__name__)
# Load config manually
app.config["DATASTATION_TOKEN"] = "9269ea4cbabe84c94ea5bf41db03f09a924f0f47"
app.config["DATASTATION_BASE_URL"] = "https://datastation.com.ng"

with app.app_context():
    print("Checking User Details with CORRECT token...")
    status, body = get_user_details()
    print(f"Status: {status}")
    print(f"Body: {body}")
