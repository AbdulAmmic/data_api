from flask import request
from models import db, User
from utils.responses import success_response, error_response
from utils.security import create_jwt, auth_required
from utils.helpers import uid

def register_auth_routes(bp):

    @bp.post("/register")
    def register():
        data = request.get_json(force=True, silent=True) or {}
        full_name = (data.get("full_name") or "").strip()
        email = (data.get("email") or "").strip().lower()
        phone = (data.get("phone") or "").strip()
        password = data.get("password") or ""

        if not full_name or not email or not password:
            return error_response("full_name, email, password are required", 400)

        if User.query.filter_by(email=email).first():
            return error_response("Email already registered", 409)

        user = User(id=uid("usr_"), full_name=full_name, email=email, phone=phone)
        user.set_password(password)
        db.session.add(user)
        # db.session.commit() # Commit later after potential account generation

        # --- Gafiapay Virtual Account Generation ---
        # We attempt this *before* final commit so we can save everything atomically,
        # or we commit user first? 
        # Better to commit user first so if API fails we still have the user?
        # User requested "creating account, logging...".
        # Let's commit user first.
        db.session.commit()

        try:
            from utils.gafiapay import generate_virtual_account
            from models import UserDedicatedAccount
            
            # Call Gafiapay API
            status, g_data = generate_virtual_account(full_name, email, phone)
            
            # Check success. 
            # API returns { "status": "success", "data": { ... } }
            if status in [200, 201] and g_data.get("status") == "success":
                acct_data = g_data.get("data", {})
                
                new_account = UserDedicatedAccount(
                    id=uid("gaf_"),
                    user_id=user.id,
                    provider="GAFIAPAY",
                    account_number=str(acct_data.get("accountNumber", "")),
                    account_name=acct_data.get("accountName", full_name),
                    bank_name=acct_data.get("bankName", "Virtual Bank"),
                    bank_slug="gafiapay-virtual", # or derived
                    reference=uid("ref_"), # or use external ref if provided
                    is_active=True
                )
                db.session.add(new_account)
                db.session.commit()
            else:
                # Log failure but don't fail registration
                print(f"Gafiapay generation failed for {email}: {status} - {g_data}")
        except Exception as e:
            print(f"Error generating virtual account: {e}")

        token = create_jwt(user.id)
        return success_response({"token": token, "user": {"id": user.id, "full_name": user.full_name, "email": user.email}}, "Registered", 201)

    @bp.post("/login")
    def login():
        data = request.get_json(force=True, silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return error_response("Invalid credentials", 401)

        token = create_jwt(user.id)
        
        # Fetch dedicated account
        from models import UserDedicatedAccount
        acct = UserDedicatedAccount.query.filter_by(user_id=user.id, is_active=True).first()
        
        user_data = {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "has_pin": user.has_pin,
            "wallet_balance": user.wallet_balance_kobo / 100.0,
            "virtual_account": {
                "bank_name": acct.bank_name,
                "account_number": acct.account_number,
                "account_name": acct.account_name
            } if acct else None
        }

        return success_response({"token": token, "user": user_data}, "Logged in", 200)

    @bp.post("/pin/set")
    @auth_required
    def set_pin():
        user = request.user
        data = request.get_json(force=True, silent=True) or {}
        
        pin = data.get("pin")
        password = data.get("password")
        
        if not pin or not password:
            return error_response("pin and password required", 400)
            
        if not user.check_password(password):
            return error_response("Invalid password", 401)
            
        if not (pin.isdigit() and len(pin) == 4):
            return error_response("PIN must be 4 digits", 400)
            
        user.set_pin(pin)
        db.session.commit()
        
        return success_response({}, "PIN set successfully")

    @bp.post("/pin/validate")
    @auth_required
    def validate_pin():
        user = request.user
        data = request.get_json(force=True, silent=True) or {}
        pin = data.get("pin")
        
        if not pin:
            return error_response("pin required", 400)
            
        if not user.check_pin(pin):
            return error_response("Invalid PIN", 401)
            
        return success_response({"valid": True}, "PIN is valid")
