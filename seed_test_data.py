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
                    full_name=f"User {i}",
                    phone=f"080{i}1112222",
                    wallet_balance_kobo=500000 # 5000 Naira
                )
                user.set_password("password")
                db.session.add(user)
                db.session.commit()
                print(f"Created user: {email}")
                
                # Create some transactions
                for j in range(3):
                    tx = WalletTransaction(
                        id=uid("tx_"),
                        user_id=user.id,
                        tx_type="CREDIT" if j % 2 == 0 else "DEBIT",
                        amount_kobo=50000 + (j * 1000),
                        status="SUCCESS",
                        narration=f"Test Transaction {j}",
                        reference=uid("ref_"),
                        provider="MANUAL"
                    )
                    db.session.add(tx)
        
        db.session.commit()
        print("Seeding complete.")

if __name__ == "__main__":
    seed_data()
