from app import app, db
from models import User, WalletTransaction
from utils.helpers import uid
import datetime

def seed_data():
    with app.app_context():
        print("Seeding test data...")
        
        # Create a few users
        for i in range(5):
            email = f"user{i}@example.com"
            if not User.query.filter_by(email=email).first():
                user = User(
                    id=uid("u_"),
                    email=email,
                    password="password", # Raw password for test
                    first_name=f"User",
                    last_name=f"{i}",
                    phone=f"080{i}1112222",
                    wallet_balance_kobo=500000 # 5000 Naira
                )
                db.session.add(user)
                db.session.commit()
                print(f"Created user: {email}")
                
                # Create some transactions
                tx = WalletTransaction(
                    id=uid("tx_"),
                    user_id=user.id,
                    tx_type="CREDIT",
                    amount_kobo=500000,
                    status="SUCCESS",
                    narration="Test Funding",
                    reference=uid("ref_"),
                    provider="MANUAL"
                )
                db.session.add(tx)
        
        db.session.commit()
        print("Seeding complete.")

if __name__ == "__main__":
    seed_data()
