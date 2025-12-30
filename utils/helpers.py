import uuid

def uid(prefix=""):
    return f"{prefix}{uuid.uuid4().hex}"

def naira_to_kobo(amount_naira: float) -> int:
    # avoid floats in production; keep for simplicity
    return int(round(amount_naira * 100))

def kobo_to_naira(amount_kobo: int) -> float:
    return round(amount_kobo / 100, 2)
