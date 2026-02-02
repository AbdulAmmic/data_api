from app import app, db
from models import User, UserDedicatedAccount

with app.app_context():
    u = User.query.first()
    if u:
        dva = UserDedicatedAccount.query.filter_by(user_id=u.id).first()
        print(f"User: {u.email}")
        if dva:
            print(f"DVA: {dva.account_number}")
        else:
            print("No DVA found. Creating one for testing...")
            # Create a fake one for testing
            dva = UserDedicatedAccount(
                id="test_dva_1",
                user_id=u.id,
                bank_name="Test Bank",
                account_number="9988776655", # Test number
                account_name=u.full_name,
                provider="GAFIAPAY",
                is_active=True
            )
            db.session.add(dva)
            db.session.commit()
            print(f"Created DVA: {dva.account_number}")
