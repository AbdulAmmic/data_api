import json
from flask import request, current_app
from models import db, WalletTransaction
from utils.responses import success_response, error_response
from utils.security import auth_required
from utils.helpers import uid, naira_to_kobo, kobo_to_naira
from utils.paystack import initialize_transaction, verify_transaction

def register_wallet_routes(bp):

    @bp.get("/me")
    @auth_required
    def wallet_me():
        user = request.user
        return success_response({
            "user_id": user.id,
            "balance_kobo": user.wallet_balance_kobo,
            "balance_naira": kobo_to_naira(user.wallet_balance_kobo),
        })

    @bp.post("/fund/initialize")
    @auth_required
    def fund_initialize():
        """
        Client sends amount_naira
        Server creates a PAYSTACK initialize transaction and returns authorization_url
        """
        user = request.user
        data = request.get_json(force=True, silent=True) or {}
        amount_naira = data.get("amount_naira")

        try:
            amount_naira = float(amount_naira)
        except Exception:
            return error_response("amount_naira must be a number", 400)

        if amount_naira <= 0:
            return error_response("amount_naira must be > 0", 400)

        amount_kobo = naira_to_kobo(amount_naira)

        reference = uid("psk_")
        tx = WalletTransaction(
            id=uid("wtx_"),
            user_id=user.id,
            tx_type="CREDIT",
            amount_kobo=amount_kobo,
            status="PENDING",
            narration="Wallet funding via Paystack",
            provider="PAYSTACK",
            reference=reference,
        )
        db.session.add(tx)
        db.session.commit()

        callback = current_app.config["PAYSTACK_CALLBACK_URL"]
        status_code, body = initialize_transaction(
            email=user.email,
            amount_kobo=amount_kobo,
            reference=reference,
            callback_url=callback,
            metadata={"user_id": user.id, "wallet_tx_id": tx.id},
        )

        tx.raw_response = body
        db.session.commit()

        if status_code not in (200, 201):
            tx.status = "FAILED"
            db.session.commit()
            return error_response("Paystack initialize failed", 502, {"paystack": body})

        # Paystack returns JSON {status, message, data:{authorization_url, access_code, reference}}
        return success_response({"reference": reference, "paystack_response": json.loads(body)}, "Initialized", 200)

    @bp.post("/fund/verify")
    @auth_required
    def fund_verify():
        """
        Client sends reference (from callback or stored)
        Server verifies with Paystack and credits wallet if successful (idempotent)
        """
        user = request.user
        data = request.get_json(force=True, silent=True) or {}
        reference = (data.get("reference") or "").strip()
        if not reference:
            return error_response("reference is required", 400)

        tx = WalletTransaction.query.filter_by(reference=reference, user_id=user.id, provider="PAYSTACK").first()
        if not tx:
            return error_response("Transaction not found", 404)

        if tx.status == "SUCCESS":
            return success_response({"reference": reference, "credited": True}, "Already credited", 200)

        status_code, body = verify_transaction(reference)
        tx.raw_response = body
        db.session.commit()

        if status_code != 200:
            tx.status = "FAILED"
            db.session.commit()
            return error_response("Paystack verify failed", 502, {"paystack": body})

        parsed = json.loads(body)
        # Expect: parsed["data"]["status"] == "success"
        pay_status = (((parsed or {}).get("data") or {}).get("status") or "").lower()
        if pay_status != "success":
            tx.status = "FAILED"
            db.session.commit()
            return error_response("Payment not successful", 400, {"paystack": parsed})

        # credit wallet (idempotent guard is tx.status)
        tx.status = "SUCCESS"
        user.wallet_balance_kobo += tx.amount_kobo
        db.session.commit()

        return success_response({
            "reference": reference,
            "credited": True,
            "new_balance_kobo": user.wallet_balance_kobo,
            "new_balance_naira": kobo_to_naira(user.wallet_balance_kobo),
            "paystack": parsed
        }, "Wallet funded", 200)

    @bp.get("/transactions")
    @auth_required
    def list_transactions():
        user = request.user
        items = WalletTransaction.query.filter_by(user_id=user.id).order_by(WalletTransaction.created_at.desc()).limit(100).all()
        data = [{
            "id": x.id,
            "type": x.tx_type,
            "amount_kobo": x.amount_kobo,
            "amount_naira": kobo_to_naira(x.amount_kobo),
            "status": x.status,
            "provider": x.provider,
            "reference": x.reference,
            "narration": x.narration,
            "created_at": x.created_at.isoformat()
        } for x in items]
        return success_response({"items": data})
