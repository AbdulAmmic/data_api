from app import app, db
from models import User
import sys

def fund_user(email_query, amount_naira):
    with app.app_context():
        # Find user
        if "@" in email_query:
            user = User.query.filter_by(email=email_query).first()
        else:
            user = User.query.filter(User.email.contains(email_query)).first()

        if not user:
            print(f"User matching '{email_query}' not found.")
            return

        amount_kobo = int(float(amount_naira) * 100)
        user.wallet_balance_kobo += amount_kobo
        db.session.commit()
        
        print(f"Successfully funded {user.email} with N{amount_naira}")
        print(f"New Balance: N{user.wallet_balance_kobo / 100}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python fund_wallet.py <email_part> <amount_naira>")
        # Default fallback for quick execution
        print("Running default: funding first user with 50000")
        with app.app_context():
            user = User.query.first()
            if user:
                user.wallet_balance_kobo += 5000000 # 50k
                db.session.commit()
                print(f"Funded {user.email} with N50,000")
    else:
        fund_user(sys.argv[1], sys.argv[2])
