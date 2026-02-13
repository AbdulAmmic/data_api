import sys
import traceback
from app import app
from models import db, User, Role, UserRole
from utils.helpers import uid
from sqlalchemy.exc import IntegrityError

print("Starting seed script...")

with app.app_context():
    print("Inside app context.")
    
    # 1. Create Admin Role
    try:
        admin_role = Role.query.filter_by(name="admin").first()
        if not admin_role:
            print("Creating admin role...")
            admin_role = Role(id=uid("role_"), name="admin")
            db.session.add(admin_role)
            db.session.commit()
            print("Admin role created.")
        else:
            print(f"Admin role exists: {admin_role.id}")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating role: {e}")
        # Continue if role exists maybe?
        admin_role = Role.query.filter_by(name="admin").first()
        if not admin_role:
             print("Critical: Admin role missing and could not be created.")
             sys.exit(1)

    # 2. Create Admin User
    try:
        email = "admin.majire@data.com"
        admin_user = User.query.filter_by(email=email).first()
        if not admin_user:
            print(f"Creating admin user {email}...")
            admin_user = User(
                id=uid("usr_"),
                full_name="Admin Majire",
                email=email,
                phone="0000000000"
            )
            admin_user.set_password("12345678")
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created.")
        else:
            print(f"Admin user exists: {admin_user.id}")
            # Reset password
            print("Resetting password...")
            admin_user.set_password("12345678")
            db.session.commit()
            print("Password reset.")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating user: {e}")
        admin_user = User.query.filter_by(email=email).first()

    # 3. Assign Role
    if admin_user and admin_role:
        try:
            user_role = UserRole.query.filter_by(user_id=admin_user.id, role_id=admin_role.id).first()
            if not user_role:
                print("Assigning admin role to user...")
                user_role = UserRole(user_id=admin_user.id, role_id=admin_role.id)
                db.session.add(user_role)
                db.session.commit()
                print("Role assigned.")
            else:
                print("User already has admin role.")
        except Exception as e:
            db.session.rollback()
            print(f"Error assigning role: {e}")

    print("Seed script completed.")
