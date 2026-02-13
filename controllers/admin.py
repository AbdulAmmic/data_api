from flask import request
from models import db, PriceItem, UserRole, User, WalletTransaction, ServicePurchase
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

    @bp.get("/users")
    @auth_required
    @admin_required
    def list_users():
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        query = request.args.get("query", "")

        q = User.query
        if query:
            q = q.filter(
                (User.email.ilike(f"%{query}%")) | 
                (User.full_name.ilike(f"%{query}%")) |
                (User.phone.ilike(f"%{query}%"))
            )
        
        pagination = q.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        
        users_list = []
        for u in pagination.items:
            is_admin = UserRole.query.filter_by(user_id=u.id, role_id="admin").first()
            users_list.append({
                "id": u.id,
                "full_name": u.full_name,
                "email": u.email,
                "phone": u.phone,
                "balance": u.wallet_balance_kobo / 100.0,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
                "is_admin": bool(is_admin)
            })

        return success_response({
            "users": users_list,
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": page
        })

    @bp.get("/stats")
    @auth_required
    @admin_required
    def get_stats():
        total_users = User.query.count()
        total_balance_kobo = db.session.query(db.func.sum(User.wallet_balance_kobo)).scalar() or 0
        pending_txs = WalletTransaction.query.filter_by(status="PENDING").count()
        # Total successful debits (sales)
        total_sales_kobo = db.session.query(db.func.sum(WalletTransaction.amount_kobo)).filter(
            WalletTransaction.tx_type == "DEBIT", 
            WalletTransaction.status == "SUCCESS"
        ).scalar() or 0

        return success_response({
            "total_users": total_users,
            "total_user_balance": total_balance_kobo / 100.0,
            "pending_transactions": pending_txs,
            "total_sales": abs(total_sales_kobo) / 100.0
        })

    @bp.get("/transactions")
    @auth_required
    @admin_required
    def list_transactions():
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        status = request.args.get("status")

        q = WalletTransaction.query
        if status:
            q = q.filter_by(status=status.upper())
        
        pagination = q.order_by(WalletTransaction.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        
        txs = [{
            "id": t.id,
            "user_id": t.user_id,
            "type": t.tx_type,
            "amount": t.amount_kobo / 100.0,
            "status": t.status,
            "narration": t.narration,
            "reference": t.reference,
            "date": t.created_at.isoformat()
        } for t in pagination.items]

        return success_response({
            "transactions": txs,
            "total": pagination.total,
            "pages": pagination.pages
        })
    
    @bp.delete("/prices/<pid>")
    @auth_required
    @admin_required
    def delete_price(pid):
        item = PriceItem.query.get(pid)
        if not item:
            return error_response("Price item not found", 404)
        
        db.session.delete(item)
        db.session.commit()
        return success_response({}, "Price item deleted")

    @bp.post("/users/<uid>/fund")
    @auth_required
    @admin_required
    def fund_user_wallet(uid):
        data = request.get_json(force=True) or {}
        amount_naira = data.get("amount")
        
        if not amount_naira:
            return error_response("amount required")
            
        user = User.query.get(uid)
        if not user:
            return error_response("User not found", 404)
            
        amount_kobo = int(float(amount_naira) * 100)
        
        # Credit user
        user.wallet_balance_kobo += amount_kobo
        
        from utils.helpers import uid as gen_uid
        # Create transaction record
        tx = WalletTransaction(
            id=gen_uid("tx_"),
            user_id=user.id,
            tx_type="CREDIT",
            amount_kobo=amount_kobo,
            status="SUCCESS",
            narration="Admin manual funding",
            reference=gen_uid("admin_fund_"),
            provider="MANUAL"
        )
        db.session.add(tx)
        db.session.commit()
        
        return success_response({"new_balance": user.wallet_balance_kobo / 100.0}, "Wallet funded")
