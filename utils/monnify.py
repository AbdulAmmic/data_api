import requests
import base64
from flask import current_app

MONNIFY_BASE = "https://sandbox.monnify.com/api/v1"
MONNIFY_SECRET_KEY= "8VK9B9LDEN6YEZV57LBNX68JGD00H0UV"
MONNIFY_API_KEY= "MK_TEST_8AXR5F87T6" 
MONNIFY_CONTRACT_CODE= "6324967932"

def get_access_token():
    api_key = MONNIFY_API_KEY
    secret = MONNIFY_SECRET_KEY

    if not api_key or not secret:
        raise RuntimeError("Monnify API credentials not configured")

    token = base64.b64encode(f"{api_key}:{secret}".encode()).decode()

    headers = {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json"
    }

    r = requests.post(f"{MONNIFY_BASE}/auth/login", headers=headers, timeout=30)
    return r.status_code, r.json()


def create_reserved_account(customer_name, email, reference):
    status, auth_res = get_access_token()

    if status != 200 or not auth_res.get("requestSuccessful"):
        return status, auth_res

    token = auth_res["responseBody"]["accessToken"]

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "accountReference": reference,
        "accountName": customer_name,
        "currencyCode": "NGN",
        "contractCode": MONNIFY_CONTRACT_CODE,
        "customerEmail": email,
        "customerName": customer_name,
        "getAllAvailableBanks": True
    }

    r = requests.post(
        f"{MONNIFY_BASE}/bank-transfer/reserved-accounts",
        json=payload,
        headers=headers,
        timeout=30
    )

    return r.status_code, r.json()
