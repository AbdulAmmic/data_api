# config.py
import os
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


class Config:
    # -----------------------------
    # BASIC APP SETTINGS
    # -----------------------------
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")

    # -----------------------------
    # DATABASE CONFIG
    # -----------------------------
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///resell_app.db"  # Default for local dev
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # -----------------------------
    # VTpass API CONFIG
    # -----------------------------
    VT_PASS_API_KEY = os.getenv("VT_PASS_API_KEY")
    VT_PASS_PUBLIC_KEY = os.getenv("VT_PASS_PUBLIC_KEY")
    VT_PASS_SECRET_KEY = os.getenv("VT_PASS_SECRET_KEY")
    VT_PASS_SECRET_KEY = os.getenv("VT_PASS_SECRET_KEY")
    VT_PASS_BASE_URL = os.getenv("VT_PASS_BASE_URL", "https://sandbox.vtpass.com/api/")

    # -----------------------------
    # GAFIAPAY CONFIG
    # -----------------------------
    GAFIAPAY_API_KEY = os.getenv("GAFIAPAY_API_KEY")
    GAFIAPAY_SECRET_KEY = os.getenv("GAFIAPAY_SECRET_KEY")
    GAFIAPAY_BASE_URL = os.getenv("GAFIAPAY_BASE_URL", "https://api.gafiapay.com/api/v1/external")

    # -----------------------------
    # CHEETAHPAY CONFIG
    # -----------------------------
    CHEETAHPAY_PUBLIC_KEY = os.getenv("CHEETAHPAY_PUBLIC_KEY")
    CHEETAHPAY_PRIVATE_KEY = os.getenv("CHEETAHPAY_PRIVATE_KEY")
    CHEETAHPAY_MODE = os.getenv("CHEETAHPAY_MODE", "test") # test or live

    # -----------------------------
    # WALLET SETTINGS
    # -----------------------------
    DEFAULT_WALLET_BALANCE = 0.00
    WALLET_PREFIX = "101"  # Used to generate unique account numbers (e.g., 10100001)

    # -----------------------------
    # BILALSADASUB CONFIG
    # -----------------------------
    BILALSADASUB_TOKEN = os.getenv("BILALSADASUB_TOKEN")
    BILALSADASUB_BASE_URL = os.getenv("BILALSADASUB_BASE_URL", "https://bilalsadasub.com")
    BILALSADASUB_USERNAME = os.getenv("BILALSADASUB_USERNAME")   # For Basic auth (balance check)
    BILALSADASUB_PASSWORD = os.getenv("BILALSADASUB_PASSWORD")   # For Basic auth (balance check)

    # -----------------------------
    # APP MODES
    # -----------------------------
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    ENV = os.getenv("FLASK_ENV", "development")


# Helper to load config dynamically
def get_config():
    env = os.getenv("FLASK_ENV", "development")
    if env == "production":
        return Config
    return Config
