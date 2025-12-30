import json
from flask import request
from models import db, WalletTransaction, User
from utils.responses import success_response, error_response
from utils.paystack import verify_webhook_signature
from utils.helpers import kobo_to_naira

def register_webhook_routes(bp):

    @bp.post("/paystack")
    def paystack_webhook():
        # Verify signature (Paystack docs: x-paystack-signature = HMAC SHA512 of raw body) :contentReference[oaicite:3]{index=3}
        signature = request.headers.get("x-paystack-signature", "")
        raw = request.get_data()  # raw bytes
        if not verify_webhook_signature(raw, signature):
            return error_response("Invalid signature", 400)

        try:
            event = json.loads(raw.decode("utf-8"))
        except Exception:
            return error_response("Invalid JSON body", 400)

        event_type = event.get("event")
        data = event.get("data") or {}

        # We only credit on successful charge
        # Typical: event == "charge.success"
        if event_type != "charge.success":
            return success_response({"received": True, "event": event_type}, "Ignored", 200)

        reference = data.get("reference")
        status = (data.get("status") or "").lower()
        amount = data.get("amount")  # kobo
        customer = (data.get("customer") or {})
        email = (customer.get("email") or "").lower()

        if status != "success" or not reference or not amount:
            return success_response({"received": True}, "No action", 200)

        tx = WalletTransaction.query.filter_by(reference=reference, provider="PAYSTACK").first()
        if not tx:
            # If you want, create a "late" tx by matching email.
            return success_response({"received": True, "note": "reference not found"}, "No action", 200)

        if tx.status == "SUCCESS":
            return success_response({"received": True, "credited": True}, "Already credited", 200)

        user = db.session.get(User, tx.user_id)
        if not user:
            tx.status = "FAILED"
            db.session.commit()
            return success_response({"received": True}, "User missing", 200)

        # Credit wallet idempotently
        tx.status = "SUCCESS"
        user.wallet_balance_kobo += int(amount)
        tx.raw_response = raw.decode("utf-8")
        db.session.commit()

        return success_response({
            "received": True,
            "credited": True,
            "reference": reference,
            "amount_naira": kobo_to_naira(int(amount)),
            "user_email": user.email
        }, "Credited", 200)
