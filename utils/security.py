import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, current_app
from models import db, User

def create_jwt(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=current_app.config["JWT_EXPIRES_HOURS"]),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")

def decode_jwt(token: str):
    return jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])

def auth_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return {"success": False, "message": "Missing Bearer token", "data": {}}, 401
        token = auth.split(" ", 1)[1].strip()
        try:
            payload = decode_jwt(token)
        except Exception:
            return {"success": False, "message": "Invalid/expired token", "data": {}}, 401

        user = db.session.get(User, payload.get("user_id"))
        if not user or not user.is_active:
            return {"success": False, "message": "User not found/inactive", "data": {}}, 401

        request.user = user
        return fn(*args, **kwargs)
    return wrapper
