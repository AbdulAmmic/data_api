from flask import request
from models import db, ServicePurchase
from utils.responses import success_response, error_response
from utils.security import auth_required
from utils.helpers import kobo_to_naira
from utils.reconcile import query_provider, normalize_provider_status
from controllers.admin import admin_required

def register_reconcile_routes(bp):

    @bp.post("/reconcile")
    @auth_required
    @admin_required
    def reconcile_transactions():
        """
        Reconcile all PENDING / FAILED transactions
        Optional body:
          {
            "service": "DATA" | "AIRTIME" | "ELECTRICITY" | "CABLE"
          }
        """
        data = request.get_json(silent=True) or {}
        service_filter = data.get("service")

        q = ServicePurchase.query.filter(
            ServicePurchase.status.in_(["PENDING", "FAILED"])
        )
        if service_filter:
            q = q.filter_by(service=service_filter)

        purchases = q.order_by(ServicePurchase.created_at.asc()).limit(200).all()

        reconciled = []
        skipped = []

        for p in purchases:
            # provider tx id may be inside response payload
            provider_tx_id = None
            if p.response_payload:
                try:
                    provider_tx_id = str(
                        (json.loads(p.response_payload) or {}).get("id")
                    )
                except Exception:
                    pass

            if not provider_tx_id:
                skipped.append(p.id)
                continue

            status_code, body = query_provider(p.service, provider_tx_id)
            if status_code != 200 or not body:
                skipped.append(p.id)
                continue

            provider_status = normalize_provider_status(body)

            if provider_status == "SUCCESS":
                p.status = "SUCCESS"
                p.response_payload = body
                db.session.commit()

                reconciled.append({
                    "purchase_id": p.id,
                    "service": p.service,
                    "amount_naira": kobo_to_naira(p.amount_kobo),
                    "status": "SUCCESS"
                })

            elif provider_status == "FAILED":
                p.status = "FAILED"
                p.response_payload = body
                db.session.commit()
                reconciled.append({
                    "purchase_id": p.id,
                    "service": p.service,
                    "status": "FAILED"
                })
            else:
                skipped.append(p.id)

        return success_response({
            "reconciled_count": len(reconciled),
            "reconciled": reconciled,
            "skipped": skipped
        }, "Reconciliation completed")
