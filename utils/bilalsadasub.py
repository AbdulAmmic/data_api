import requests
import base64
from flask import current_app

def _headers():
    """
    Bilalsadasub purchase endpoints use: Authorization: Token <token>
    """
    token = (current_app.config.get("BILALSADASUB_TOKEN") or "").strip()
    
    # Ensure prefix
    if token and not token.startswith("Token "):
        token = f"Token {token}"

    return {
        "Authorization": token,
        "Content-Type": "application/json",
    }

def _basic_headers():
    """
    Bilalsadasub /api/user endpoint uses Basic auth (username:password base64).
    Falls back to Token auth if credentials not configured.
    """
    username = (current_app.config.get("BILALSADASUB_USERNAME") or "").strip()
    password = (current_app.config.get("BILALSADASUB_PASSWORD") or "").strip()
    if username and password:
        encoded = base64.b64encode(f"{username}:{password}".encode()).decode()
        return {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json",
        }
    # Fallback to Token if no credentials configured
    return _headers()

def _base():
    return (current_app.config.get("BILALSADASUB_BASE_URL") or "https://bilalsadasub.com").rstrip("/")

def get_user_details():
    """
    POST /api/user with Basic auth to get balance and token.
    (GET with Token auth returns 500 on Bilalsadasub)
    """
    url = f"{_base()}/api/user"
    r = requests.post(url, headers=_basic_headers(), timeout=30)
    return r.status_code, r.text

# -------------------------
# DATA
# -------------------------
def buy_data(payload: dict):
    """
    POST /api/data
    Payload keys: network, phone, data_plan, bypass, request-id
    """
    url = f"{_base()}/api/data"
    r = requests.post(url, json=payload, headers=_headers(), timeout=30)
    return r.status_code, r.text

def list_data_transactions(params: dict | None = None):
    url = f"{_base()}/api/data"
    r = requests.get(url, params=params or {}, headers=_headers(), timeout=30)
    return r.status_code, r.text

# -------------------------
# AIRTIME TOPUP
# -------------------------
def buy_airtime_topup(payload: dict):
    """
    POST /api/topup
    Payload keys: network, phone, plan_type, amount, bypass, request-id
    """
    url = f"{_base()}/api/topup"
    r = requests.post(url, json=payload, headers=_headers(), timeout=30)
    return r.status_code, r.text

# -------------------------
# ELECTRICITY BILLPAYMENT
# -------------------------
def buy_bill_payment(payload: dict):
    """
    POST /api/bill
    Payload keys: disco, meter_type, meter_number, amount, bypass, request-id
    """
    url = f"{_base()}/api/bill"
    r = requests.post(url, json=payload, headers=_headers(), timeout=30)
    return r.status_code, r.text

# -------------------------
# CABLE SUBSCRIPTION
# -------------------------
def buy_cable_subscription(payload: dict):
    """
    POST /api/cable
    Payload keys: cable, iuc, cable_plan, bypass, request-id
    """
    url = f"{_base()}/api/cable"
    r = requests.post(url, json=payload, headers=_headers(), timeout=30)
    return r.status_code, r.text

# -------------------------
# VALIDATION ENDPOINTS
# -------------------------
def validate_iuc(iuc: str, cable: str):
    """
    GET /api/cable/cable-validation?iuc=...&cable=...
    """
    url = f"{_base()}/api/cable/cable-validation"
    params = {"iuc": iuc, "cable": cable}
    r = requests.get(url, params=params, headers=_headers(), timeout=30)
    return r.status_code, r.text

def validate_meter(meter_number: str, disco: str, meter_type: str):
    """
    GET /api/bill/bill-validation?meter_number=...&disco=...&meter_type=...
    """
    url = f"{_base()}/api/bill/bill-validation"
    params = {"meter_number": meter_number, "disco": disco, "meter_type": meter_type}
    r = requests.get(url, params=params, headers=_headers(), timeout=30)
    return r.status_code, r.text

# -------------------------
# PINS & CARDS
# -------------------------
def generate_airtime_pin(network: int, plan_type: int, quantity: int, card_name: str):
    """
    POST /api/recharge_card
    Payload keys: network, plan_type, quantity, card_name, request-id
    """
    url = f"{_base()}/api/recharge_card"
    payload = {
        "network": network,
        "plan_type": plan_type,
        "quantity": quantity,
        "card_name": card_name,
    }
    r = requests.post(url, json=payload, headers=_headers(), timeout=30)
    return r.status_code, r.text

def buy_data_card(payload: dict):
    """
    POST /api/data_card
    Payload keys: network, plan_type, quantity, card_name, request-id
    """
    url = f"{_base()}/api/data_card"
    r = requests.post(url, json=payload, headers=_headers(), timeout=30)
    return r.status_code, r.text

def generate_epin(payload: dict):
    """
    POST /api/exam
    Payload keys: exam, quantity, request-id
    """
    url = f"{_base()}/api/exam"
    # payload expected: exam, quantity
    r = requests.post(url, json=payload, headers=_headers(), timeout=30)
    return r.status_code, r.text
