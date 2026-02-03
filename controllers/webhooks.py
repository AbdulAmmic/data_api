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

    # =================================================
    # 🔹 3. GAFIAPAY WEBHOOK (VIRTUAL ACCOUNT)
    # =================================================
    @bp.post("/gafiapay")
    def gafiapay_webhook():
        # Gafiapay sends JSON payload
        try:
            data = request.get_json(force=True)
        except Exception:
            return error_response("Invalid JSON", 400)

        # Log for debugging
        print(f"Set Gafiapay Webhook: {json.dumps(data, indent=2)}")

        # Extract fields (Adjust based on actual Gafiapay docs if available, assuming standard)
        # Assuming structure: { "event": "transaction.successful", "data": { "reference": "...", "amount": 100, "virtual_account_number": "..." } }
        # OR direct: { "reference": "...", "amount": 100, "account_number": "..." }
        
        # Let's handle a generic structure that covers common patterns or matches what we simulated
        
        # 1. Check Event Type
        event_type = data.get("event", "").lower()
        if "payment.received" not in event_type and "success" not in event_type:
             return success_response({"received": True}, f"Ignored event: {event_type}", 200)

        # 2. Extract Data
        # Support both structures: Nested 'transaction' (from logs) and flat (legacy/documented?)
        
        payload = data.get("data", {})
        transaction = payload.get("transaction", {})
        
        # Dictionary to hold extracted values
        vals = {
            "ref": None,
            "amt": None,
            "acct": None
        }

        if transaction:
            # Struct: data -> transaction -> metadata -> virtualAccountNo
            vals["ref"] = transaction.get("orderNo") or transaction.get("id")
            vals["amt"] = transaction.get("amount")
            meta = transaction.get("metadata", {})
            vals["acct"] = meta.get("virtualAccountNo") or meta.get("virtualAccountNo", "")
        else:
            # Fallback to flat/direct structure
            target = payload if payload else data
            vals["ref"] = target.get("reference") or target.get("tx_ref")
            vals["amt"] = target.get("amount")
            vals["acct"] = target.get("virtual_account_number") or target.get("account_number")
        
        reference = vals["ref"]
        amount = vals["amt"]
        account_number = vals["acct"]
        
        if not reference or not amount or not account_number:
            print(f"Missing fields: ref={reference}, amt={amount}, acct={account_number}")
            return success_response({"received": True}, "Missing critical fields", 200)

        # 3. Find User by Dedicated Account
        dva = UserDedicatedAccount.query.filter_by(
            account_number=account_number,
            is_active=True
        ).first()

        if not dva:
             return success_response({"received": True}, "Account not found", 200)

        user = db.session.get(User, dva.user_id)
        if not user:
             return success_response({"received": True}, "User not found", 200)

        # 4. Check for Duplicate Transaction
        existing = WalletTransaction.query.filter_by(
            reference=reference,
            provider="GAFIAPAY"
        ).first()

        if existing:
             return success_response({"received": True, "duplicate": True}, "Already processed", 200)

        # 5. Credit Wallet
        # Convert amount to Kobo. Gafiapay usually sends Naira (e.g. 500.00)
        try:
            amount_naira = float(amount)
            amount_kobo = int(amount_naira * 100)
        except ValueError:
            return error_response("Invalid amount format", 400)

        tx = WalletTransaction(
            id=uid("wtx_"),
            user_id=user.id,
            tx_type="CREDIT",
            amount_kobo=amount_kobo,
            status="SUCCESS",
            narration=f"Wallet funding via Gafiapay Transfer ({account_number})",
            provider="GAFIAPAY",
            reference=reference,
            raw_response=json.dumps(data),
        )

        user.wallet_balance_kobo += amount_kobo
        db.session.add(tx)
        db.session.commit()

        print(f"CREDITED {user.email} with N{amount_naira}")

        return success_response(
            {
                "credited": True,
                "amount_naira": amount_naira,
                "user": user.email
            },
            "Wallet funded successfully",
            200
        )
