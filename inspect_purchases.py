from app import app
from models import ServicePurchase
import json

with app.app_context():
    # Get last 5 data purchases
    purchases = ServicePurchase.query.filter_by(service="DATA").order_by(ServicePurchase.created_at.desc()).limit(5).all()
    for p in purchases:
        print(f"ID: {p.id} | Status: {p.status} | Time: {p.created_at}")
        print(f"Payload: {p.request_payload}")
        print(f"Response: {p.response_payload}")
        print("-" * 50)
