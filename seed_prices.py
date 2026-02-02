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
            # DATA - MTN
            {"service": "DATA", "provider_code": "mtn_sme-1gb", "cost": 350, "markup": 0},
            {"service": "DATA", "provider_code": "mtn_sme-2gb", "cost": 700, "markup": 0},
            {"service": "DATA", "provider_code": "mtn_sme-3gb", "cost": 950, "markup": 0},
             {"service": "DATA", "provider_code": "mtn_sme-5gb", "cost": 1500, "markup": 0},
            
            # DATA - AIRTEL
             {"service": "DATA", "provider_code": "airtel_sme-1gb", "cost": 380, "markup": 0},
             {"service": "DATA", "provider_code": "airtel_sme-2gb", "cost": 760, "markup": 0},
             
            # DATA - GLO
             {"service": "DATA", "provider_code": "glo_sme-1gb", "cost": 360, "markup": 0},
             
             # EPIN
             {"service": "EPIN", "provider_code": "waec", "cost": 3500, "markup": 0},
             {"service": "EPIN", "provider_code": "neco", "cost": 1200, "markup": 0},
             
             # CABLE
             {"service": "CABLE", "provider_code": "dstv_compact", "cost": 12500, "markup": 0},
             {"service": "CABLE", "provider_code": "dstv_premium", "cost": 21000, "markup": 0},
             {"service": "CABLE", "provider_code": "gotv_max", "cost": 4150, "markup": 0},
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
