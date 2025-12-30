from flask import request
from models import db, PriceItem, UserRole
from utils.responses import success_response, error_response
from utils.security import auth_required
from utils.helpers import uid

def admin_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = request.user
        is_admin = UserRole.query.filter_by(user_id=user.id, role_id="admin").first()
        if not is_admin:
            return error_response("Admin access required", 403)
        return fn(*args, **kwargs)
    return wrapper

def register_admin_routes(bp):

    @bp.post("/prices")
    @auth_required
    @admin_required
    def create_price():
        data = request.get_json(force=True) or {}

        service = data.get("service")
        provider_code = data.get("provider_code")
        provider_cost_naira = data.get("provider_cost_naira")
        markup_type = data.get("markup_type", "FLAT")
        markup_value = float(data.get("markup_value", 0))

        if not service or not provider_code or provider_cost_naira is None:
            return error_response("service, provider_code, provider_cost_naira required")

        item = PriceItem(
            id=uid("price_"),
            service=service,
            provider_code=provider_code,
            provider_cost_kobo=int(float(provider_cost_naira) * 100),
            markup_type=markup_type,
            markup_value=markup_value,
        )
        db.session.add(item)
        db.session.commit()

        return success_response({
            "id": item.id,
            "selling_price_naira": item.selling_price_kobo() / 100
        }, "Price created", 201)

    @bp.get("/prices")
    @auth_required
    @admin_required
    def list_prices():
        items = PriceItem.query.order_by(PriceItem.created_at.desc()).all()
        return success_response({
            "items": [{
                "id": x.id,
                "service": x.service,
                "provider_code": x.provider_code,
                "provider_cost_naira": x.provider_cost_kobo / 100,
                "markup_type": x.markup_type,
                "markup_value": x.markup_value,
                "selling_price_naira": x.selling_price_kobo() / 100,
                "active": x.is_active
            } for x in items]
        })

    @bp.patch("/prices/<pid>")
    @auth_required
    @admin_required
    def update_price(pid):
        item = PriceItem.query.get(pid)
        if not item:
            return error_response("Price not found", 404)

        data = request.get_json(force=True) or {}
        if "markup_type" in data:
            item.markup_type = data["markup_type"]
        if "markup_value" in data:
            item.markup_value = float(data["markup_value"])
        if "active" in data:
            item.is_active = bool(data["active"])

        db.session.commit()
        return success_response({
            "selling_price_naira": item.selling_price_kobo() / 100
        }, "Updated")
