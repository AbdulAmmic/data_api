from app import app
from models import PriceItem
with app.app_context():
    for net in ["mtn", "glo", "airtel"]:
        p = PriceItem.query.filter_by(network=net).first()
        if p:
            print(f"Network: {net}, ID: {p.id}, Name: {p.name}")
        else:
            print(f"Network: {net} NOT FOUND")
