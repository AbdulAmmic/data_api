from flask import request
from models import db, User
from utils.responses import success_response, error_response
from utils.security import create_jwt
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
        db.session.commit()

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
        return success_response({"token": token, "user": {"id": user.id, "full_name": user.full_name, "email": user.email}}, "Logged in", 200)
