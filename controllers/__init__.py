from flask import Blueprint

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
wallet_bp = Blueprint("wallet", __name__, url_prefix="/api/wallet")
services_bp = Blueprint("services", __name__, url_prefix="/api/services")
webhooks_bp = Blueprint("webhooks", __name__, url_prefix="/webhooks")
