import requests
from flask import current_app

def _headers():
    """
    DataStation auth varies in the wild:
    - Some docs show: Authorization: Bearer <token>
    - Your earlier snippet shows: Authorization: Token <token>

    So we expect DATASTATION_TOKEN to already include the correct prefix, e.g.:
    - "Bearer xxxxx"
    - "Token xxxxx"
    """
    token = (current_app.config.get("DATASTATION_TOKEN") or "").strip()
    return {
        "Authorization": token,
        "Content-Type": "application/json",
    }

def _base():
    return (current_app.config.get("DATASTATION_BASE_URL") or "https://datastation.com.ng").rstrip("/")

def get_user_details():
    url = f"{_base()}/api/user/"
    r = requests.get(url, headers=_headers(), timeout=30)
    return r.status_code, r.text

# -------------------------
# DATA
# -------------------------
def buy_data(payload: dict):
    """
    POST /api/data/
    Payload depends on your plan structure. Example keys often include:
      network, plan, phone, reference
    """
    url = f"{_base()}/api/data/"
    r = requests.post(url, json=payload, headers=_headers(), timeout=30)
    return r.status_code, r.text

def list_data_transactions(params: dict | None = None):
    url = f"{_base()}/api/data/"
    r = requests.get(url, params=params or {}, headers=_headers(), timeout=30)
    return r.status_code, r.text

def get_data_transaction(tx_id: str):
    url = f"{_base()}/api/data/{tx_id}"
    r = requests.get(url, headers=_headers(), timeout=30)
    return r.status_code, r.text

# -------------------------
# AIRTIME TOPUP
# -------------------------
def buy_airtime_topup(payload: dict):
    """
    POST /api/topup/
    Example keys often include:
      network, amount, phone, reference
    """
    url = f"{_base()}/api/topup/"
    r = requests.post(url, json=payload, headers=_headers(), timeout=30)
    return r.status_code, r.text

def list_airtime_topups(params: dict | None = None):
    """
    Some providers support GET /api/topup/ for listing.
    If DataStation doesn't, this may return 405/404. We expose it anyway.
    """
    url = f"{_base()}/api/topup/"
    r = requests.get(url, params=params or {}, headers=_headers(), timeout=30)
    return r.status_code, r.text

def get_airtime_topup(tx_id: str):
    """
    Expected: GET /api/topup/{id}
    Your collection had a placeholder mistake for query airtime; this is the logical endpoint.
    """
    url = f"{_base()}/api/topup/{tx_id}"
    r = requests.get(url, headers=_headers(), timeout=30)
    return r.status_code, r.text

# -------------------------
# ELECTRICITY BILLPAYMENT
# -------------------------
def buy_bill_payment(payload: dict):
    """
    POST /api/billpayment/
    Common keys:
      disco/disconame, meter_number/meternumber, amount, meter_type/mtype, phone, reference
    """
    url = f"{_base()}/api/billpayment/"
    r = requests.post(url, json=payload, headers=_headers(), timeout=30)
    return r.status_code, r.text

def list_bill_payments(params: dict | None = None):
    url = f"{_base()}/api/billpayment/"
    r = requests.get(url, params=params or {}, headers=_headers(), timeout=30)
    return r.status_code, r.text

def get_bill_payment(tx_id: str):
    url = f"{_base()}/api/billpayment/{tx_id}"
    r = requests.get(url, headers=_headers(), timeout=30)
    return r.status_code, r.text

# -------------------------
# CABLE SUBSCRIPTION
# -------------------------
def buy_cable_subscription(payload: dict):
    """
    POST /api/cablesub/
    Common keys:
      cablename/cable_name, smart_card_number/iuc, package, amount, phone, reference
    """
    url = f"{_base()}/api/cablesub/"
    r = requests.post(url, json=payload, headers=_headers(), timeout=30)
    return r.status_code, r.text

def list_cable_subscriptions(params: dict | None = None):
    url = f"{_base()}/api/cablesub/"
    r = requests.get(url, params=params or {}, headers=_headers(), timeout=30)
    return r.status_code, r.text

def get_cable_subscription(tx_id: str):
    url = f"{_base()}/api/cablesub/{tx_id}"
    r = requests.get(url, headers=_headers(), timeout=30)
    return r.status_code, r.text

# -------------------------
# VALIDATION ENDPOINTS
# -------------------------
def validate_iuc(smart_card_number: str, cablename: str):
    url = f"{_base()}/ajax/validate_iuc"
    params = {"smart_card_number": smart_card_number, "cablename": cablename}
    r = requests.get(url, params=params, headers=_headers(), timeout=30)
    return r.status_code, r.text

def validate_meter(meter_number: str, disconame: str, mtype: str):
    url = f"{_base()}/ajax/validate_meter_number"
    params = {"meternumber": meter_number, "disconame": disconame, "mtype": mtype}
    r = requests.get(url, params=params, headers=_headers(), timeout=30)
    return r.status_code, r.text

# -------------------------
# PINS (already in your earlier snippet, retained)
# -------------------------
def generate_airtime_pin(network: int, network_amount: int, quantity: int, name_on_card: str):
    url = f"{_base()}/api/rechargepin/"
    payload = {
        "network": network,
        "network_amount": network_amount,
        "quantity": quantity,
        "name_on_card": name_on_card,
    }
    r = requests.post(url, json=payload, headers=_headers(), timeout=30)
    return r.status_code, r.text

def generate_epin(exam_name: str, quantity: int):
    url = f"{_base()}/api/epin/"
    payload = {"exam_name": exam_name, "quantity": quantity}
    r = requests.post(url, json=payload, headers=_headers(), timeout=30)
    return r.status_code, r.text
