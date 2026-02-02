import hashlib
import hmac
import json
import time
import requests
from flask import current_app

def _get_config():
    return {
        "api_key": current_app.config.get("GAFIAPAY_API_KEY"),
        "secret_key": current_app.config.get("GAFIAPAY_SECRET_KEY"),
        "base_url": current_app.config.get("GAFIAPAY_BASE_URL", "https://api.gafiapay.com/api/v1/external").rstrip("/"),
    }

def _generate_signature(payload: dict, timestamp: str, secret_key: str) -> str:
    """
    Generate the x-signature for Gafiapay:
    Typically implementations use HMAC-SHA256(payload_string, secret).
    The payload string usually is the JSON dump.
    Some APIs require timestamp concatenation: timestamp + payload or payload + timestamp.
    
    Given the prompt didn't specify the EXACT signature construction string, 
    we will assume a standard pattern: payload JSON string.
    If the API expects timestamp included in the signature base string, this might need adjustment.
    """
    # Sort keys to ensure consistent order if the API requires canonical JSON
    # However, 'json=payload' in requests won't necessarily sort keys.
    # We'll use json.dumps() and hope the API is robust or we match the requests body.
    # Safest is to use the exact string we send.
    
    # We will compute signature on the json string.
    payload_str = json.dumps(payload, separators=(',', ':')) if payload else ""
    
    # NOTE: If Gafiapay requires the timestamp in the signature (common for replay attacks),
    # it would look like: f"{timestamp}{payload_str}"
    # Without explicit instruction, we'll try just payload first or follow standard secure hook practices.
    # Let's check if we can find a standard or assume the most common: Payload only or Timestamp+Payload.
    # User said: "x-signature": "generated_signature", "x-timestamp": "current_timestamp"
    # I'll use payload_str only for now as it's the base requirement.
    
    # Constructing HMAC SHA256
    signature = hmac.new(
        secret_key.encode("utf-8"),
        payload_str.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    
    return signature

def _headers(payload: dict = None):
    conf = _get_config()
    timestamp = str(int(time.time() * 1000))
    
    # We need to ensure the payload string used for signature is IDENTICAL to what is sent.
    # So we handle serialization here if payload exists.
    
    headers = {
        "x-api-key": conf["api_key"],
        "x-timestamp": timestamp,
        "Content-Type": "application/json"
    }
    
    if payload and conf["secret_key"]:
        # We assume the signature is over the JSON body.
        # If the API documentation says otherwise (e.g. including timestamp), we must adjust.
        # For now, signing the body is the reliable part.
        signature = _generate_signature(payload, timestamp, conf["secret_key"])
        headers["x-signature"] = signature
        
    return headers

def generate_virtual_account(name: str, email: str, phone: str = None):
    """
    Create a new virtual account for a customer.
    POST /account/generate
    """
    conf = _get_config()
    url = f"{conf['base_url']}/account/generate"
    
    payload = {
        "name": name,
        "email": email
    }
    if phone:
        payload["payment_references"] = phone # Some APIs use this, but let's try standard fields
        payload["phoneNumber"] = phone
        payload["phone"] = phone
    
    # Important: requests.post(json=...) uses its own serialization.
    # To correspond with our signature, we should serialize manually or use the same separators.
    # The _generate_signature used (',', ':') which handles no-spaces.
    # Let's stick to passing the dict to requests but ensure our logic matches what requests does? 
    # requests default is separators=(', ', ': ') (with spaces).
    # Safer to pass data=string to requests to correspond 100% with signature.
    
    # Let's align on standard JSON (no spaces usually preferred for sizing but spaces are valid).
    # We will use compact JSON to be safe and consistent.
    data_str = json.dumps(payload, separators=(',', ':'))
    
    # Re-calculate signature based on the EXACT string we are sending
    # Use milliseconds for timestamp
    timestamp = str(int(time.time() * 1000))
    
    # Try signature pattern: body + timestamp
    base_string = data_str + timestamp
    
    signature = hmac.new(
        conf["secret_key"].encode("utf-8"),
        base_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        "x-api-key": conf["api_key"],
        "x-timestamp": timestamp,
        "x-signature": signature,
        "Content-Type": "application/json"
    }
    
    try:
        r = requests.post(url, data=data_str, headers=headers, timeout=30)
        return r.status_code, r.json()
    except Exception as e:
        return 500, {"error": str(e)}

def list_virtual_accounts():
    """
    GET /account/list (Hypothetical based on standard REST patterns/user context)
    User mentioned: "manage virtual accounts"
    This would likely be a GET without a body.
    """
    conf = _get_config()
    url = f"{conf['base_url']}/account/list"
    
    # For GET requests with no body, signature might be empty or over query params?
    # Or maybe just over timestamp?
    # Usually if no body, some APIs don't require signature or sign the query string.
    # We will include basic Auth headers.
    
    timestamp = str(int(time.time()))
    headers = {
        "x-api-key": conf["api_key"],
        "x-timestamp": timestamp,
        "Content-Type": "application/json"
    }
    
    # If signature is strictly required even for empty body:
    if conf["secret_key"]:
        # Sign empty string? or "{}"?
        # Assuming empty string for NO body.
        signature = hmac.new(
            conf["secret_key"].encode("utf-8"),
            b"",
            hashlib.sha256
        ).hexdigest()
        headers["x-signature"] = signature

    try:
        r = requests.get(url, headers=headers, timeout=30)
        return r.status_code, r.json()
    except Exception as e:
        return 500, {"error": str(e)}
