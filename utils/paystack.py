import hmac
import hashlib
import requests
from flask import current_app

PAYSTACK_BASE = "https://api.paystack.co"


def _headers():
    return {
        "Authorization": f"Bearer {current_app.config['PAYSTACK_SECRET_KEY']}",
        "Content-Type": "application/json",
    }


def initialize_transaction(
    email: str,
    amount_kobo: int,
    reference: str,
    callback_url: str,
    metadata: dict | None = None,
):
    payload = {
        "email": email,
        "amount": int(amount_kobo),  # MUST be kobo
        "reference": reference,
        "callback_url": callback_url,
        "metadata": metadata or {},
    }

    r = requests.post(
        f"{PAYSTACK_BASE}/transaction/initialize",
        json=payload,
        headers=_headers(),
        timeout=30,
    )

    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, {"error": r.text}


def verify_transaction(reference: str):
    r = requests.get(
        f"{PAYSTACK_BASE}/transaction/verify/{reference}",
        headers=_headers(),
        timeout=30,
    )

    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, {"error": r.text}


def verify_webhook_signature(raw_body: bytes, signature: str) -> bool:
    secret = current_app.config["PAYSTACK_SECRET_KEY"].encode("utf-8")
    computed = hmac.new(secret, raw_body, hashlib.sha512).hexdigest()
    return hmac.compare_digest(computed, signature or "")

def create_customer(email: str, full_name: str, phone: str | None = None):
    payload = {
        "email": email,
        "first_name": full_name.split(" ")[0],
        "last_name": " ".join(full_name.split(" ")[1:]) or "User",
        "phone": phone,
    }

    r = requests.post(
        f"{PAYSTACK_BASE}/customer",
        json=payload,
        headers=_headers(),
        timeout=30,
    )

    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, {"error": r.text}


def create_dedicated_account(customer_code: str, preferred_bank: str = "wema-bank"):
    payload = {
        "customer": customer_code,
        "preferred_bank": preferred_bank
    }

    r = requests.post(
        f"{PAYSTACK_BASE}/dedicated_account",
        json=payload,
        headers=_headers(),
        timeout=30,
    )

    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, {"error": r.text}
