import os
from flask import Flask
from dotenv import load_dotenv
from models import db
from controllers.routes import register_routes

load_dotenv()

def create_app():
    app = Flask(__name__)

    # Core config
    app.config["SECRET_KEY"] = os.getenv("APP_SECRET_KEY", "dev_secret")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "jwt_dev_secret")
    app.config["JWT_EXPIRES_HOURS"] = int(os.getenv("JWT_EXPIRES_HOURS", "72"))

    # DB
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///app.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Paystack
    app.config["PAYSTACK_SECRET_KEY"] = os.getenv("PAYSTACK_SECRET_KEY", "")
    app.config["PAYSTACK_PUBLIC_KEY"] = os.getenv("PAYSTACK_PUBLIC_KEY", "")
    app.config["PAYSTACK_CALLBACK_URL"] = os.getenv("PAYSTACK_CALLBACK_URL", "")

    # DataStation
    app.config["DATASTATION_TOKEN"] = os.getenv("DATASTATION_TOKEN", "")
    app.config["DATASTATION_BASE_URL"] = os.getenv("DATASTATION_BASE_URL", "https://datastation.com.ng")

    # Init DB
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Routes
    register_routes(app)

    @app.get("/health")
    def health():
        return {"ok": True, "service": "vtu-wallet-api"}

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
