import json
from flask import Flask
from utils.peyflex import list_data_plans, list_cable_subscriptions

app = Flask(__name__)
app.config['PEYFLEX_BASE_URL'] = "https://client.peyflex.com.ng"
app.config['PEYFLEX_TOKEN'] = "7B0n0D6Bv1s2F5Xz1r0T0m4Bw7X9m5N9D9P9o9k0A7z8U2j2O1L1D0A8G3Y1W4Q0J"

with app.app_context():
    # Fetch MTN Gifting Plans
    status, body = list_data_plans("mtn_gifting_data")
    print("MTN Data Status:", status)
    
    try:
        mtn_plans = json.loads(body)
        print("MTN Plans:", json.dumps(mtn_plans.get('plans', [])[:2], indent=2))
    except Exception as e:
        print("Body parsing failed:", body[:200])
        
    # Fetch GOTV Cable Plans
    status, body = list_cable_subscriptions("gotv")
    print("GOTV Cable Status:", status)
    try:
        cable_plans = json.loads(body)
        print("GOTV Plans:", json.dumps(cable_plans.get('plans', [])[:2], indent=2))
    except Exception as e:
        pass
