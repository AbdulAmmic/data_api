
from app import app
from models import PriceItem

# app = create_app() (Removed)

with app.app_context():
    items = PriceItem.query.all()
    print(f"Total PriceItems: {len(items)}")
    for item in items:
        print(f"{item.service} - {item.provider_code}")
