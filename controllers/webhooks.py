import json
from flask import request
from models import db, WalletTransaction, User, UserDedicatedAccount
from utils.responses import success_response, error_response
from utils.paystack import verify_webhook_signature
from utils.helpers import kobo_to_naira, uid


def register_webhook_routes(bp):

    @bp.post("/paystack")
    def paystack_webhook():
        # -------------------------------------------------
        # VERIFY PAYSTACK SIGNATURE
        # -------------------------------------------------
        signature = request.headers.get("x-paystack-signature", "")
        raw = request.get_data()

        if not verify_webhook_signature(raw, signature):
            return error_response("Invalid signature", 400)

        try:
            event = json.loads(raw.decode("utf-8"))
        except Exception:
            return error_response("Invalid JSON body", 400)

        event_type = event.get("event")
        data = event.get("data") or {}

        # -------------------------------------------------
        # ONLY PROCESS SUCCESSFUL CHARGES
        # -------------------------------------------------
        if event_type != "charge.success":
            return success_response(
                {"received": True, "event": event_type},
                "Ignored",
                200
            )

        status = (data.get("status") or "").lower()
        amount_kobo = int(data.get("amount") or 0)
        reference = data.get("reference")

        if status != "success" or not amount_kobo:
            return success_response({"received": True}, "No action", 200)

        # =================================================
        # 🔹 1. DEDICATED VIRTUAL ACCOUNT (BANK TRANSFER)
        # =================================================
        authorization = data.get("authorization") or {}
        receiver_account = authorization.get("receiver_bank_account_number")

        if receiver_account:
            dva = UserDedicatedAccount.query.filter_by(
                account_number=receiver_account,
                is_active=True
            ).first()

            if dva:
                user = db.session.get(User, dva.user_id)

                if not user:
                    return success_response({"received": True}, "User missing", 200)

                # Prevent duplicate credit
                existing = WalletTransaction.query.filter_by(
                    reference=reference,
                    provider="PAYSTACK"
                ).first()

                if not existing:
                    tx = WalletTransaction(
                        id=uid("wtx_"),
                        user_id=user.id,
                        tx_type="CREDIT",
                        amount_kobo=amount_kobo,
                        status="SUCCESS",
                        narration="Wallet funding via bank transfer",
                        provider="PAYSTACK",
                        reference=reference,
                        raw_response=json.dumps(data),
                    )
                    user.wallet_balance_kobo += amount_kobo
                    db.session.add(tx)
                    db.session.commit()

                return success_response(
                    {
                        "credited": True,
                        "method": "DVA",
                        "amount_naira": kobo_to_naira(amount_kobo),
                        "user_email": user.email
                    },
                    "Wallet funded via DVA",
                    200
                )

        # =================================================
        # 🔹 2. PAYSTACK CHECKOUT (CARD / USSD / TRANSFER)
        # =================================================
        if not reference:
            return success_response({"received": True}, "No reference", 200)

        tx = WalletTransaction.query.filter_by(
            reference=reference,
            provider="PAYSTACK"
        ).first()

        if not tx:
            return success_response(
                {"received": True, "note": "reference not found"},
                "No action",
                200
            )

        if tx.status == "SUCCESS":
            return success_response(
                {"received": True, "credited": True},
                "Already credited",
                200
            )

        user = db.session.get(User, tx.user_id)
        if not user:
            tx.status = "FAILED"
            db.session.commit()
            return success_response({"received": True}, "User missing", 200)

        # Amount mismatch protection
        if amount_kobo != tx.amount_kobo:
            tx.status = "FAILED"
            tx.raw_response = json.dumps(data)
            db.session.commit()
            return success_response(
                {
                    "received": True,
                    "error": "Amount mismatch",
                    "expected_kobo": tx.amount_kobo,
                    "paid_kobo": amount_kobo
                },
                "Rejected",
                200
            )

        # Credit wallet (idempotent)
        tx.status = "SUCCESS"
        user.wallet_balance_kobo += amount_kobo
        tx.raw_response = json.dumps(data)
        db.session.commit()

        return success_response(
            {
                "received": True,
                "credited": True,
                "reference": reference,
                "amount_naira": kobo_to_naira(amount_kobo),
                "user_email": user.email
            },
            "Wallet funded via Paystack",
            200
        )
