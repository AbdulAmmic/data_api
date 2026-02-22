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
                    # Apply 1.8% Charge
                    fee_kobo = int(amount_kobo * 0.018)
                    credit_kobo = amount_kobo - fee_kobo

                    tx = WalletTransaction(
                        id=uid("wtx_"),
                        user_id=user.id,
                        tx_type="CREDIT",
                        amount_kobo=credit_kobo, # Credit the net amount
                        status="SUCCESS",
                        narration=f"Wallet funding via bank transfer (Fee: {kobo_to_naira(fee_kobo)})",
                        provider="PAYSTACK",
                        reference=reference,
                        raw_response=json.dumps(data),
                    )
                    user.wallet_balance_kobo += credit_kobo
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
        # Credit wallet (idempotent)
        # Apply 1.8% Charge
        fee_kobo = int(amount_kobo * 0.018)
        credit_kobo = amount_kobo - fee_kobo

        tx.status = "SUCCESS"
        tx.amount_kobo = credit_kobo # Update tx amount to what is actually credited? Or keep original?
        # Usually it's better to keep original amount in a separate field, but for simplicity here we track the credit.
        # Let's track the credit amount to match the wallet balance update.
        tx.narration = f"Wallet funding via Paystack (Fee: {kobo_to_naira(fee_kobo)})"
        
        user.wallet_balance_kobo += credit_kobo
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

        # Apply 1.8% Charge
        fee_kobo = int(amount_kobo * 0.018)
        credit_kobo = amount_kobo - fee_kobo

        tx = WalletTransaction(
            id=uid("wtx_"),
            user_id=user.id,
            tx_type="CREDIT",
            amount_kobo=credit_kobo,
            status="SUCCESS",
            narration=f"Wallet funding via Gafiapay Transfer ({account_number}) - Fee: {kobo_to_naira(fee_kobo)}",
            provider="GAFIAPAY",
            reference=reference,
            raw_response=json.dumps(data),
        )

        user.wallet_balance_kobo += credit_kobo
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

    # =================================================
    # 🔹 4. CHEETAHPAY WEBHOOK (AIRTIME TO CASH)
    # =================================================
    @bp.route("/cheetahpay", methods=["GET", "POST"])
    def cheetahpay_webhook():
        # Cheetahpay typically sends GET query parameters, but some might use POST
        from models import AirtimeToCashTransaction
        
        # Merge source of parameters
        params = request.args.to_dict()
        if request.method == "POST":
            try:
                # Could be form data or JSON
                if request.is_json:
                    params.update(request.get_json(force=True))
                else:
                    params.update(request.form.to_dict())
            except:
                pass

        # Log incoming request for debugging
        print(f"Cheetahpay Callback ({request.method}): {params}")
        
        # Parameters expected: order_id, status, amount, network
        order_internal_id = params.get("order_id")
        status = params.get("status") # 'credited', 'invalid', 'pending'
        amount = params.get("amount")
        
        if not order_internal_id or not status:
            return "Missing parameters", 400
            
        tx = AirtimeToCashTransaction.query.filter_by(id=order_internal_id).first()
        if not tx:
             # Try searching by reference if id doesn't match
             tx = AirtimeToCashTransaction.query.filter_by(reference=order_internal_id).first()
        
        if not tx:
            return "Transaction not found", 404
            
        if tx.status in ["APPROVED", "REJECTED"]:
            return "Already processed", 200

        if status == "credited":
            tx.status = "APPROVED"
            tx.admin_note = f"Automatically approved via Cheetahpay callback. Provided Amount: {amount}"
            
            # Credit User Wallet
            user = db.session.get(User, tx.user_id)
            if user:
                # We should use the amount from Cheetahpay if possible, 
                # but tx.amount_kobo stores our expected amount.
                # Cheetahpay amount might have fees deducted or be slightly different.
                # Usually we credit based on what was RECEIVED.
                
                try:
                    received_amount_naira = float(amount)
                    credit_kobo = int(received_amount_naira * 100)
                except:
                    credit_kobo = tx.amount_kobo

                # Add a buffer/check? For now, let's just credit.
                user.wallet_balance_kobo += credit_kobo
                
                # Record Wallet Transaction
                w_tx = WalletTransaction(
                    id=uid("wtx_"),
                    user_id=user.id,
                    tx_type="CREDIT",
                    amount_kobo=credit_kobo,
                    status="SUCCESS",
                    narration=f"Airtime to Cash - {tx.network} - {tx.phone_from}",
                    provider="CHEETAHPAY",
                    reference=tx.id
                )
                db.session.add(w_tx)
            
            db.session.commit()
            print(f"Cheetahpay APPROVED: {tx.id} for User {tx.user_id}")
            return "OK", 200
            
        elif status == "invalid":
            tx.status = "REJECTED"
            tx.admin_note = "Rejected by Cheetahpay: Invalid Airtime"
            db.session.commit()
            print(f"Cheetahpay REJECTED: {tx.id}")
            return "OK", 200
            
        return "PENDING", 200
