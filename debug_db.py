from app import app
from models import PriceItem

with app.app_context():
    plans = PriceItem.query.all()
    print(f"Total PriceItems: {len(plans)}")
    for p in plans:
        print(f"ID: '{p.id}', Service: '{p.service}', Active: {p.is_active}, ProviderCode: {p.provider_code}")
