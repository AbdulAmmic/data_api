import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from models import db
from controllers.routes import register_routes
from utils.responses import error_response

load_dotenv()


def create_app():
    app = Flask(__name__)

    # -----------------------------
    # CORS (SAFE & CORRECT)
    # -----------------------------
    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )

    # -----------------------------
    # App Config
    # -----------------------------
    app.config["SECRET_KEY"] = os.getenv("APP_SECRET_KEY", "dev_secret")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "jwt_dev_secret")
    app.config["JWT_EXPIRES_HOURS"] = int(os.getenv("JWT_EXPIRES_HOURS", "72"))

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:///app.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Paystack
    app.config["PAYSTACK_SECRET_KEY"] = os.getenv("PAYSTACK_SECRET_KEY", "")
    app.config["PAYSTACK_PUBLIC_KEY"] = os.getenv("PAYSTACK_PUBLIC_KEY", "")
    app.config["PAYSTACK_CALLBACK_URL"] = os.getenv("PAYSTACK_CALLBACK_URL", "")

    # Bilalsadasub (Replacing Datastation)
    app.config["BILALSADASUB_TOKEN"] = os.getenv("BILALSADASUB_TOKEN", os.getenv("DATASTATION_TOKEN", ""))
    app.config["BILALSADASUB_BASE_URL"] = os.getenv(
        "BILALSADASUB_BASE_URL", os.getenv("DATASTATION_BASE_URL", "https://bilalsadasub.com")
    )
    
    # Keep Datastation keys as aliases for backward compatibility (points to Bilalsadasub)
    app.config["DATASTATION_TOKEN"] = app.config["BILALSADASUB_TOKEN"]
    app.config["DATASTATION_BASE_URL"] = app.config["BILALSADASUB_BASE_URL"]

    # Gafiapay
    app.config["GAFIAPAY_API_KEY"] = os.getenv("GAFIAPAY_API_KEY", "")
    app.config["GAFIAPAY_SECRET_KEY"] = os.getenv("GAFIAPAY_SECRET_KEY", "")
    app.config["GAFIAPAY_BASE_URL"] = os.getenv(
        "GAFIAPAY_BASE_URL", "https://api.gafiapay.com/api/v1/external"
    )

    # -----------------------------
    # Database Init
    # -----------------------------
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # -----------------------------
    # Routes
    # -----------------------------
    register_routes(app)

    @app.get("/health")
    def health():
        routes = [str(p) for p in app.url_map.iter_rules()]
        return {"ok": True, "service": "vtu-wallet-api", "routes": routes}

    @app.errorhandler(Exception)
    def handle_exception(e):
        """Global error handler to ensure JSON is always returned."""
        # Optional: app.logger.error(f"Server Error: {str(e)}")
        message = str(e)
        # Avoid leaking too much info in production if you want, 
        # but for debugging 'invalid json' it's better to see the error.
        return error_response(f"Internal Server Error: {message}", 500)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "False").lower() == "true",
    )
