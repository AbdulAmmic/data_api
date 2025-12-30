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

def initialize_transaction(email: str, amount_kobo: int, reference: str, callback_url: str, metadata: dict | None = None):
    payload = {
        "email": email,
        "amount": amount_kobo,
        "reference": reference,
        "callback_url": callback_url,
        "metadata": metadata or {},
    }
    r = requests.post(f"{PAYSTACK_BASE}/transaction/initialize", json=payload, headers=_headers(), timeout=30)
    return r.status_code, r.text

def verify_transaction(reference: str):
    r = requests.get(f"{PAYSTACK_BASE}/transaction/verify/{reference}", headers=_headers(), timeout=30)
    return r.status_code, r.text

def verify_webhook_signature(raw_body: bytes, signature: str) -> bool:
    secret = current_app.config["PAYSTACK_SECRET_KEY"].encode("utf-8")
    computed = hmac.new(secret, raw_body, hashlib.sha512).hexdigest()
    return hmac.compare_digest(computed, signature or "")
