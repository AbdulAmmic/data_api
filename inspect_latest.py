from app import app
from models import ServicePurchase
from datetime import datetime, timedelta

with app.app_context():
    # Get last 1 purchase
    p = ServicePurchase.query.order_by(ServicePurchase.created_at.desc()).first()
    if p:
        print(f"ID: {p.id} | Status: {p.status} | Time: {p.created_at}")
        print(f"Payload: {p.request_payload}")
        print(f"Response: {p.response_payload}")
    else:
        print("No purchases found.")
