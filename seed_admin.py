from app import create_app
from models import db, User, Role, UserRole
from utils.helpers import uid

app = create_app()

with app.app_context():
    # 1. Create Admin Role if not exists
    admin_role = Role.query.filter_by(name="admin").first()
    if not admin_role:
        print("Creating admin role...")
        admin_role = Role(id=uid("role_"), name="admin")
        db.session.add(admin_role)
    else:
        print("Admin role exists.")

    # 2. Create Admin User if not exists
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
        db.session.flush() # get id
    else:
        print("Admin user exists.")

    # 3. Assign Role
    user_role = UserRole.query.filter_by(user_id=admin_user.id, role_id=admin_role.id).first()
    if not user_role:
        print("Assigning admin role to user...")
        user_role = UserRole(user_id=admin_user.id, role_id=admin_role.id)
        db.session.add(user_role)
    else:
        print("User already has admin role.")

    db.session.commit()
    print("Done.")
