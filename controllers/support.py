from flask import Blueprint, request
from models import db, Complaint, User
from utils.responses import success_response, error_response
from utils.security import auth_required
from utils.helpers import uid
from controllers.admin import admin_required

support_bp = Blueprint("support", __name__, url_prefix="/api/support")
admin_support_bp = Blueprint("admin_support", __name__, url_prefix="/api/admin/complaints")

# --- USER ENDPOINTS ---

@support_bp.post("/complaints")
@auth_required
def create_complaint():
    user = request.user
    data = request.get_json(force=True, silent=True) or {}
    
    subject = data.get("subject")
    message = data.get("message")
    
    if not subject or not message:
        return error_response("Subject and message are required", 400)
        
    complaint = Complaint(
        id=uid("tkt_"),
        user_id=user.id,
        subject=subject,
        message=message,
        status="OPEN"
    )
    
    db.session.add(complaint)
    db.session.commit()
    
    return success_response({
        "id": complaint.id,
        "subject": complaint.subject,
        "status": complaint.status,
        "created_at": complaint.created_at.isoformat()
    }, "Complaint submitted successfully", 201)

@support_bp.get("/complaints")
@auth_required
def get_my_complaints():
    user = request.user
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    
    pagination = Complaint.query.filter_by(user_id=user.id)\
        .order_by(Complaint.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
        
    items = []
    for c in pagination.items:
        items.append({
            "id": c.id,
            "subject": c.subject,
            "message": c.message,
            "status": c.status,
            "admin_reply": c.admin_reply,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat() if c.updated_at else None
        })
        
    return success_response({
        "complaints": items,
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": page
    })

# --- ADMIN ENDPOINTS ---

@admin_support_bp.get("")
@auth_required
@admin_required
def list_all_complaints():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    status = request.args.get("status")
    
    q = Complaint.query
    if status:
        q = q.filter_by(status=status.upper())
        
    pagination = q.order_by(Complaint.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
        
    items = []
    for c in pagination.items:
        # Fetch user details efficiently? 
        # In a real app we might join, but for now lazy load is okay or we assume small scale.
        user = User.query.get(c.user_id)
        user_email = user.email if user else "Unknown"
        
        items.append({
            "id": c.id,
            "user_email": user_email,
            "subject": c.subject,
            "message": c.message,
            "status": c.status,
            "admin_reply": c.admin_reply,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat() if c.updated_at else None
        })
        
    return success_response({
        "complaints": items,
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": page
    })

@admin_support_bp.patch("/<tkt_id>/resolve")
@auth_required
@admin_required
def resolve_complaint(tkt_id):
    data = request.get_json(force=True, silent=True) or {}
    reply = data.get("reply")
    new_status = data.get("status", "RESOLVED")
    
    complaint = Complaint.query.get(tkt_id)
    if not complaint:
        return error_response("Complaint not found", 404)
        
    if reply:
        complaint.admin_reply = reply
    
    complaint.status = new_status
    db.session.commit()
    
    return success_response({
        "id": complaint.id,
        "status": complaint.status,
        "admin_reply": complaint.admin_reply
    }, "Complaint updated")

def register_support_routes(app):
    app.register_blueprint(support_bp)
    app.register_blueprint(admin_support_bp)
