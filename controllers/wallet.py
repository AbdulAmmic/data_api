import json
from flask import request, current_app
from models import db, WalletTransaction
from utils.responses import success_response, error_response
from utils.security import auth_required
from utils.helpers import uid, naira_to_kobo, kobo_to_naira
from utils.paystack import initialize_transaction, verify_transaction
from models import db, WalletTransaction, UserDedicatedAccount
from utils.paystack import create_customer, create_dedicated_account
from utils.monnify import create_reserved_account

def register_wallet_routes(bp):

    @bp.get("/me")
    @auth_required
    def wallet_me():
        user = request.user
        balance = user.wallet_balance_kobo or 0
        return success_response({
            "user_id": user.id,
            "balance_kobo": balance,
            "balance_naira": kobo_to_naira(balance),
        })

    # -------------------------------------------------
    # INITIALIZE PAYSTACK FUNDING
    # -------------------------------------------------
    @bp.post("/fund/initialize")
    @auth_required
    def fund_initialize():
        """
        Client sends amount_naira
        Server creates a PAYSTACK initialize transaction
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
            metadata={
                "user_id": user.id,
                "wallet_tx_id": tx.id
            },
        )

        # store full response safely
        tx.raw_response = json.dumps(body)
        db.session.commit()

        if status_code not in (200, 201) or not body.get("status"):
            tx.status = "FAILED"
            db.session.commit()
            return error_response(
                "Paystack initialize failed",
                502,
                {"paystack": body}
            )

        return success_response({
            "reference": reference,
            "paystack_response": body
        }, "Initialized", 200)

    # -------------------------------------------------
    # VERIFY PAYSTACK FUNDING (FALLBACK)
    # -------------------------------------------------
    @bp.post("/fund/verify")
    @auth_required
    def fund_verify():
        """
        Fallback verification.
        Webhook should be the primary credit path.
        """
        user = request.user
        data = request.get_json(force=True, silent=True) or {}
        reference = (data.get("reference") or "").strip()

        if not reference:
            return error_response("reference is required", 400)

        tx = WalletTransaction.query.filter_by(
            reference=reference,
            user_id=user.id,
            provider="PAYSTACK"
        ).first()

        if not tx:
            return error_response("Transaction not found", 404)

        if tx.status == "SUCCESS":
            return success_response(
                {"reference": reference, "credited": True},
                "Already credited",
                200
            )

        status_code, body = verify_transaction(reference)

        tx.raw_response = json.dumps(body)
        db.session.commit()

        if status_code != 200 or not body.get("status"):
            tx.status = "FAILED"
            db.session.commit()
            return error_response(
                "Paystack verify failed",
                502,
                {"paystack": body}
            )

        data_block = body.get("data") or {}
        pay_status = (data_block.get("status") or "").lower()

        if pay_status != "success":
            tx.status = "FAILED"
            db.session.commit()
            return error_response(
                "Payment not successful",
                400,
                {"paystack": body}
            )

        paid_kobo = int(data_block.get("amount") or 0)
        if paid_kobo != tx.amount_kobo:
            tx.status = "FAILED"
            db.session.commit()
            return error_response(
                "Amount mismatch",
                400,
                {
                    "expected_kobo": tx.amount_kobo,
                    "paid_kobo": paid_kobo
                }
            )

        # credit wallet (idempotent)
        balance = user.wallet_balance_kobo or 0
        user.wallet_balance_kobo = balance + tx.amount_kobo
        tx.status = "SUCCESS"
        db.session.commit()

        return success_response({
            "reference": reference,
            "credited": True,
            "new_balance_kobo": user.wallet_balance_kobo,
            "new_balance_naira": kobo_to_naira(user.wallet_balance_kobo),
            "paystack": body
        }, "Wallet funded", 200)

    # -------------------------------------------------
    # LIST TRANSACTIONS
    # -------------------------------------------------
    @bp.get("/transactions")
    @auth_required
    def list_transactions():
        user = request.user
        items = (
            WalletTransaction.query
            .filter_by(user_id=user.id)
            .order_by(WalletTransaction.created_at.desc())
            .limit(100)
            .all()
        )

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
    @bp.post("/dedicated-account")
    @auth_required
    def create_or_get_dedicated_account():
        user = request.user

        # If already created, return it
        existing = UserDedicatedAccount.query.filter_by(user_id=user.id).first()
        if existing:
            return success_response({
                "account_number": existing.account_number,
                "bank_name": existing.bank_name,
                "account_name": existing.account_name
            }, "Dedicated account exists")

        # 1. Create Paystack customer if missing
        if not user.paystack_customer_code:
            status, res = create_customer(
                email=user.email,
                full_name=user.full_name,
                phone=user.phone
            )
            if status != 200 or not res.get("status"):
                return error_response("Failed to create Paystack customer", 502, res)

            user.paystack_customer_code = res["data"]["customer_code"]
            db.session.commit()

        # 2. Create dedicated account
        status, res = create_dedicated_account(user.paystack_customer_code)
        if status != 200 or not res.get("status"):
            return error_response("Failed to create dedicated account", 502, res)

        data = res["data"]

        dva = UserDedicatedAccount(
            id=uid("dva_"),
            user_id=user.id,
            paystack_customer_code=user.paystack_customer_code,
            paystack_dedicated_account_id=str(data["id"]),
            account_number=data["account_number"],
            account_name=data["account_name"],
            bank_name=data["bank"]["name"],
            bank_slug=data["bank"]["slug"],
        )

        db.session.add(dva)
        db.session.commit()

        return success_response({
            "account_number": dva.account_number,
            "bank_name": dva.bank_name,
            "account_name": dva.account_name
        }, "Dedicated account created")


    @bp.post("/dedicated-account_monnify")
    @auth_required
    def create_dedicated_account():
        user = request.user

        # 1. Check local DB first
        existing = UserDedicatedAccount.query.filter_by(
            user_id=user.id,
            provider="MONNIFY",
            is_active=True
        ).first()

        if existing:
            return success_response({
                "account_number": existing.account_number,
                "bank_name": existing.bank_name,
                "account_name": existing.account_name
            }, "Existing account")

        reference = uid("mnf_")
        status, res = create_reserved_account(user.full_name, user.email, reference)

        # 2. If Monnify says already exists
        if res.get("responseCode") == "R42":
            # At this point Monnify already has the account
            # You MUST fetch it from Monnify (or ask support if fetch API not enabled)
            return error_response(
                "Monnify account already exists for this user. Please contact support to fetch existing account.",
                409,
                res
            )

        # 3. Normal failure
        if status != 200 or not res.get("requestSuccessful"):
            return error_response("Failed to create Monnify account", 502, res)

        body = res.get("responseBody") or {}

        # 4. Defensive parsing
        if isinstance(body.get("accounts"), list) and body["accounts"]:
            acc = body["accounts"][0]
        elif body.get("accountNumber"):
            acc = body
        else:
            return error_response("Invalid Monnify response structure", 502, res)

        # 5. Save locally
        dva = UserDedicatedAccount(
            id=uid("dva_"),
            user_id=user.id,
            provider="MONNIFY",
            account_number=acc.get("accountNumber"),
            bank_name=acc.get("bankName"),
            account_name=acc.get("accountName"),
            reference=reference
        )

        db.session.add(dva)
        db.session.commit()

        return success_response({
            "account_number": dva.account_number,
            "bank_name": dva.bank_name,
            "account_name": dva.account_name
        }, "Monnify account created")
