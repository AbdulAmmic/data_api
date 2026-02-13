print("Importing flask...")
from flask import Flask

print("Importing models...")
from models import db, User

print("Importing controllers.admin...")
try:
    from controllers.admin import register_admin_routes
    print("Imported controllers.admin")
except Exception as e:
    print(f"Failed to import controllers.admin: {e}")

print("Importing app...")
try:
    from app import create_app
    print("Imported app")
except Exception as e:
    print(f"Failed to import app: {e}")
