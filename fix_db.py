from app import app
from models import db, PriceItem
from utils.helpers import uid

def fix():
    with app.app_context():
        # Frontend sends 'mtn', 'airtel', 'glo', '9mobile'
        # Backend looks for service='AIRTIME' and provider_code=network
        networks = ["mtn", "airtel", "glo", "9mobile"]
        
        print("Fixing Airtime prices...")
        for net in networks:
            exists = PriceItem.query.filter_by(service="AIRTIME", provider_code=net).first()
            if not exists:
                print(f"Adding missing price for: {net}")
                item = PriceItem(
                    id=uid("prc_"),
                    service="AIRTIME",
                    provider_code=net,
                    provider_cost_kobo=0,
                    markup_type="FLAT",
                    markup_value=0,
                    is_active=True
                )
                db.session.add(item)
            else:
                print(f"Price for {net} already exists.")
                
        db.session.commit()
        print("Database update complete.")

if __name__ == "__main__":
    fix()
