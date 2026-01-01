from flask import Blueprint

from controllers import auth_bp, wallet_bp, services_bp, webhooks_bp
from controllers.auth import register_auth_routes
from controllers.wallet import register_wallet_routes
from controllers.services import register_service_routes
from controllers.webhooks import register_webhook_routes
from controllers.reconcile import register_reconcile_routes




def register_routes(app):
    # Register route handlers
    register_auth_routes(auth_bp)
    register_wallet_routes(wallet_bp)
    register_service_routes(services_bp)
    register_webhook_routes(webhooks_bp)
    register_reconcile_routes(admin_bp)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(wallet_bp)
    app.register_blueprint(services_bp)
    app.register_blueprint(webhooks_bp)
    app.register_blueprint(admin_bp)

# ADMIN BLUEPRINT (separate from services)
admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")
