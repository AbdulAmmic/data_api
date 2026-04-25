from app import app
from models import PriceItem
with app.app_context():
    # Check for any "gitfing" typo
    typos = PriceItem.query.filter(PriceItem.id.ilike("%gitfing%")).all()
    if typos:
        print(f"Found {len(typos)} typos!")
        for t in typos:
            print(f"Typo ID: {t.id}")
    else:
        print("No typos found in ID.")
