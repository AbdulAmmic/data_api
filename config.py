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
    VT_PASS_BASE_URL = os.getenv("VT_PASS_BASE_URL", "https://sandbox.vtpass.com/api/")

    # -----------------------------
    # WALLET SETTINGS
    # -----------------------------
    DEFAULT_WALLET_BALANCE = 0.00
    WALLET_PREFIX = "101"  # Used to generate unique account numbers (e.g., 10100001)

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
