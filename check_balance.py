from app import app, db
from models import User

with app.app_context():
    try:
        users = User.query.all()
        for u in users:
            balance_naira = u.wallet_balance_kobo / 100
            print(f"User: {u.full_name} | Email: {u.email} | Balance: N{balance_naira}")
    except Exception as e:
        print(f"Error: {e}")
