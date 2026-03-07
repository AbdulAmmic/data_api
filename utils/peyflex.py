import requests
from flask import current_app

def _headers():
    token = (current_app.config.get("PEYFLEX_TOKEN") or "7B0n0D6Bv1s2F5Xz1r0T0m4Bw7X9m5N9D9P9o9k0A7z8U2j2O1L1D0A8G3Y1W4Q0J").strip()
    
    # Ensure prefix
    if not token.startswith("Token ") and not token.startswith("Bearer "):
        token = f"Bearer {token}"

    return {
        "Authorization": token,
        "Content-Type": "application/json",
    }

def _base():
    return (current_app.config.get("PEYFLEX_BASE_URL") or "https://client.peyflex.com.ng").rstrip("/")

def get_user_details():
    url = f"{_base()}/api/user/profile/"
    r = requests.get(url, headers=_headers(), timeout=30)
    return r.status_code, r.text

def get_wallet_balance():
    url = f"{_base()}/api/wallet/balance/"
    r = requests.get(url, headers=_headers(), timeout=30)
    return r.status_code, r.text

# -------------------------
# DATA
# -------------------------
def buy_data(payload: dict):
    url = f"{_base()}/api/data/purchase/"
    r = requests.post(url, json=payload, headers=_headers(), timeout=30)
    return r.status_code, r.text

def list_data_networks():
    url = f"{_base()}/api/data/networks/"
    r = requests.get(url, headers=_headers(), timeout=30)
    return r.status_code, r.text

def list_data_plans(network: str):
    url = f"{_base()}/api/data/plans/?network={network}"
    r = requests.get(url, headers=_headers(), timeout=30)
    return r.status_code, r.text

# -------------------------
# AIRTIME TOPUP
# -------------------------
def buy_airtime_topup(payload: dict):
    url = f"{_base()}/api/airtime/topup/"
    r = requests.post(url, json=payload, headers=_headers(), timeout=30)
    return r.status_code, r.text

def list_airtime_networks():
    url = f"{_base()}/api/airtime/networks/"
    r = requests.get(url, headers=_headers(), timeout=30)
    return r.status_code, r.text

# -------------------------
# ELECTRICITY BILLPAYMENT
# -------------------------
def buy_bill_payment(payload: dict):
    url = f"{_base()}/api/electricity/subscribe/"
    r = requests.post(url, json=payload, headers=_headers(), timeout=30)
    return r.status_code, r.text

def list_bill_payments(params: dict | None = None):
    url = f"{_base()}/api/electricity/plans/?identifier=electricity"
    r = requests.get(url, params=params or {}, headers=_headers(), timeout=30)
    return r.status_code, r.text

# -------------------------
# CABLE SUBSCRIPTION
# -------------------------
def buy_cable_subscription(payload: dict):
    url = f"{_base()}/api/cable/subscribe/"
    r = requests.post(url, json=payload, headers=_headers(), timeout=30)
    return r.status_code, r.text

def list_cable_subscriptions(provider: str):
    url = f"{_base()}/api/cable/plans/{provider}/"
    r = requests.get(url, headers=_headers(), timeout=30)
    return r.status_code, r.text

# -------------------------
# VALIDATION ENDPOINTS
# -------------------------
def validate_iuc(smart_card_number: str, cablename: str):
    url = f"{_base()}/api/cable/verify/"
    payload = {"iuc": smart_card_number, "identifier": cablename}
    r = requests.post(url, json=payload, headers=_headers(), timeout=30)
    return r.status_code, r.text

def validate_meter(meter_number: str, disconame: str, mtype: str):
    url = f"{_base()}/api/electricity/verify/?identifier=electricity&meter={meter_number}&plan={disconame}&type={mtype}"
    r = requests.get(url, headers=_headers(), timeout=30)
    return r.status_code, r.text
