from app import create_app
from models import db, PriceItem
from utils.helpers import uid

app = create_app()

def seed_prices():
    with app.app_context():
        print("Seeding prices...")
        
        # Clear existing
        PriceItem.query.delete()
        
        plans = [
            # AIRTIME (Generic for VTU)
            # These act as flags to enable airtime for the network.
            # Cost is 0 (ignored), Markup is 0 (sold at face value).
            # If you want to give discounts, set markup_type="PERCENT" and markup_value=-2.0 (for 2% discount)
            {"service": "AIRTIME", "provider_code": "mtn", "cost": 0, "markup": 0},
            {"service": "AIRTIME", "provider_code": "glo", "cost": 0, "markup": 0},
            {"service": "AIRTIME", "provider_code": "airtel", "cost": 0, "markup": 0},
            {"service": "AIRTIME", "provider_code": "9mobile", "cost": 0, "markup": 0},
            
            # AIRTIME PIN (Example denominations)
            # This logic still uses DB. If you want to use PINs, uncomment/add more.
            # {"service": "AIRTIME_PIN", "provider_code": "mtn_100", "cost": 98, "markup": 2}, # Sell at 100
            
            # Note: DATA, CABLE, ELECTRICITY, EPIN are now managed via config files in /plans directory.
            # They are NOT seeded here anymore.
        ]

        for p in plans:
            item = PriceItem(
                id=uid("prc_"),
                service=p["service"],
                provider_code=p["provider_code"],
                provider_cost_kobo=p["cost"] * 100, # Convert to kobo
                markup_type="FLAT",
                markup_value=p["markup"],
                is_active=True
            )
            db.session.add(item)
        
        db.session.commit()
        print("Prices seeded.")

if __name__ == "__main__":
    seed_prices()
