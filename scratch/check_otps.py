from app import create_app
from models import db, User
from datetime import datetime

app = create_app()

with app.app_context():
    # Check for users with reset tokens set within the last 24 hours
    users = User.query.filter(User.reset_token != None).all()
    print(f"Total users with a reset token: {len(users)}")
    
    for u in users:
        print(f"Email: {u.email}")
        print(f"Token: {u.reset_token}")
        print(f"Expiry: {u.reset_token_expiry}")
        print("-" * 20)

    if not users:
        print("No active reset tokens found in the database.")
