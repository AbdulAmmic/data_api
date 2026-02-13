from app import create_app
from models import db, User, Role, UserRole

app = create_app()

with app.app_context():
    email = "admin.majire@data.com"
    user = User.query.filter_by(email=email).first()
    
    if not user:
        print(f"User {email} NOT FOUND.")
    else:
        print(f"User found: {user.id}")
        print(f"Password Hash: {user.password_hash}")
        
        # Test password
        is_valid = user.check_password("12345678")
        print(f"Password '12345678' valid: {is_valid}")
        
        # Check roles
        roles = UserRole.query.filter_by(user_id=user.id).all()
        print(f"Roles: {[r.role_id for r in roles]}")
        
        if not is_valid:
            print("Resetting password to '12345678'...")
            user.set_password("12345678")
            db.session.commit()
            print("Password reset.")
            
            # Re-test
            print(f"Re-test valid: {user.check_password('12345678')}")
