from app import app
from models import PriceItem

with app.app_context():
    data_count = PriceItem.query.filter_by(service="DATA").count()
    airtime_count = PriceItem.query.filter_by(service="AIRTIME").count()
    cable_count = PriceItem.query.filter_by(service="CABLE").count()
    print(f"DATA: {data_count}")
    print(f"AIRTIME: {airtime_count}")
    print(f"CABLE: {cable_count}")
    
    if data_count == 0:
        print("WARNING: No data plans found!")
    
    # Print sample data plan
    sample = PriceItem.query.filter(PriceItem.service == "DATA", PriceItem.id.contains("sme")).first()
    if sample:
        print(f"Sample SME ID: {sample.id}")
        print(f"Sample Name: {sample.name}")
    else:
        print("WARNING: No SME IDs found!")
