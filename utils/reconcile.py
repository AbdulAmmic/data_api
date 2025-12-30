import json
from models import db, ServicePurchase
from utils.datastation import (
    get_data_transaction,
    get_airtime_topup,
    get_bill_payment,
    get_cable_subscription
)

SERVICE_QUERY_MAP = {
    "DATA": get_data_transaction,
    "AIRTIME": get_airtime_topup,
    "ELECTRICITY": get_bill_payment,
    "CABLE": get_cable_subscription,
}

def query_provider(service: str, provider_tx_id: str):
    fn = SERVICE_QUERY_MAP.get(service)
    if not fn:
        return None, None
    return fn(provider_tx_id)

def normalize_provider_status(body: str) -> str:
    """
    Try to infer SUCCESS / FAILED from provider response.
    This is defensive because providers are inconsistent.
    """
    try:
        data = json.loads(body)
    except Exception:
        return "UNKNOWN"

    text = json.dumps(data).lower()

    if "success" in text or "successful" in text:
        return "SUCCESS"
    if "failed" in text or "error" in text:
        return "FAILED"

    return "UNKNOWN"
