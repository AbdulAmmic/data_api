from app import app, db
from models import User, WalletTransaction, AirtimeToCashTransaction, ServicePurchase, Role, UserRole, UserDedicatedAccount, PriceItem

with app.app_context():
    try:
        print("Creating all tables in Neon DB...")
        db.create_all()
        print("Tables created successfully!")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error creating tables: {e}")
