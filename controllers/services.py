import json
from flask import request
from models import db, ServicePurchase, WalletTransaction
from utils.responses import success_response, error_response
from utils.security import auth_required
from utils.helpers import uid, kobo_to_naira
from utils.pricing import get_price_or_fail
from utils.datastation import (
    buy_data,
    buy_airtime_topup,
    buy_bill_payment,
    buy_cable_subscription,
    validate_meter,
    validate_iuc,
    generate_airtime_pin,
    generate_epin
)

# ---------------------------------------------------------
# SERVICE ROUTES (WALLET-BASED + SERVER PRICING)
# ---------------------------------------------------------

def register_service_routes(bp):

    # -----------------------------
    # Wallet helpers
    # -----------------------------
    def _debit_wallet(user, amount_kobo: int, narration: str):
        if user.wallet_balance_kobo < amount_kobo:
            return None, error_response("Insufficient wallet balance", 400, {
                "balance_naira": kobo_to_naira(user.wallet_balance_kobo)
            })

        user.wallet_balance_kobo -= amount_kobo

        tx = WalletTransaction(
            id=uid("wtx_"),
            user_id=user.id,
            tx_type="DEBIT",
            amount_kobo=amount_kobo,
            status="SUCCESS",
            narration=narration,
            provider="DATASTATION",
            reference=uid("ds_")
        )
        db.session.add(tx)
        db.session.commit()
        return tx, None

    def _refund_wallet(user, amount_kobo: int, narration: str):
        user.wallet_balance_kobo += amount_kobo
        tx = WalletTransaction(
            id=uid("rf_"),
            user_id=user.id,
            tx_type="CREDIT",
            amount_kobo=amount_kobo,
            status="SUCCESS",
            narration=narration,
            provider="INTERNAL_REFUND",
            reference=uid("refund_")
        )
        db.session.add(tx)
        db.session.commit()

    def _create_purchase(user, service, amount_kobo, payload):
        purchase = ServicePurchase(
            id=uid("sp_"),
            user_id=user.id,
            service=service,
            amount_kobo=amount_kobo,
            status="PENDING",
            provider="DATASTATION",
            request_payload=json.dumps(payload)
        )
        db.session.add(purchase)
        db.session.commit()
        return purchase

    # =====================================================
    # VALIDATIONS (FREE)
    # =====================================================
    @bp.get("/validate/meter")
    @auth_required
    def validate_meter_route():
        meter = request.args.get("meternumber")
        disco = request.args.get("disconame")
        mtype = request.args.get("mtype")

        if not meter or not disco or not mtype:
            return error_response("meternumber, disconame, mtype required")

        status, body = validate_meter(meter, disco, mtype)
        if status != 200:
            return error_response("Meter validation failed", 502, {"provider": body})

        return success_response({"provider_response": body})

    @bp.get("/validate/iuc")
    @auth_required
    def validate_iuc_route():
        iuc = request.args.get("smart_card_number")
        cable = request.args.get("cablename")

        if not iuc or not cable:
            return error_response("smart_card_number, cablename required")

        status, body = validate_iuc(iuc, cable)
        if status != 200:
            return error_response("IUC validation failed", 502, {"provider": body})

        return success_response({"provider_response": body})

    # =====================================================
    # DATA PURCHASE
    # =====================================================
    @bp.post("/data/buy")
    @auth_required
    def buy_data_route():
        user = request.user
        data = request.get_json(force=True)

        network = data.get("network")
        plan = data.get("plan")
        phone = data.get("phone")

        if not network or not plan or not phone:
            return error_response("network, plan, phone required")

        provider_code = f"{network}_{plan}"
        price = get_price_or_fail("DATA", provider_code)
        if not price:
            return error_response("Data plan not available", 400)

        amount_kobo = price.selling_price_kobo()

        payload = {
            "network": network,
            "plan": plan,
            "phone": phone,
            "reference": uid("ref_")
        }

        purchase = _create_purchase(user, "DATA", amount_kobo, payload)
        debit, err = _debit_wallet(user, amount_kobo, "Data purchase")
        if err:
            purchase.status = "FAILED"
            db.session.commit()
            return err

        status, body = buy_data(payload)
        purchase.response_payload = body

        if status not in (200, 201):
            purchase.status = "FAILED"
            db.session.commit()
            _refund_wallet(user, amount_kobo, "Refund: Data failed")
            return error_response("Data purchase failed", 502, {"provider": body})

        purchase.status = "SUCCESS"
        db.session.commit()

        return success_response({
            "purchase_id": purchase.id,
            "amount_naira": kobo_to_naira(amount_kobo),
            "provider_response": body
        }, "Data purchased")

    # =====================================================
    # AIRTIME TOPUP
    # =====================================================
    @bp.post("/airtime/topup")
    @auth_required
    def airtime_topup_route():
        user = request.user
        data = request.get_json(force=True)

        network = data.get("network")
        phone = data.get("phone")
        amount = data.get("amount")

        if not network or not phone or not amount:
            return error_response("network, phone, amount required")

        provider_code = f"{network}_{amount}"
        price = get_price_or_fail("AIRTIME", provider_code)
        if not price:
            return error_response("Airtime amount not available", 400)

        amount_kobo = price.selling_price_kobo()

        payload = {
            "network": network,
            "amount": amount,
            "phone": phone,
            "reference": uid("ref_")
        }

        purchase = _create_purchase(user, "AIRTIME", amount_kobo, payload)
        debit, err = _debit_wallet(user, amount_kobo, "Airtime topup")
        if err:
            purchase.status = "FAILED"
            db.session.commit()
            return err

        status, body = buy_airtime_topup(payload)
        purchase.response_payload = body

        if status not in (200, 201):
            purchase.status = "FAILED"
            db.session.commit()
            _refund_wallet(user, amount_kobo, "Refund: Airtime failed")
            return error_response("Airtime failed", 502, {"provider": body})

        purchase.status = "SUCCESS"
        db.session.commit()

        return success_response({
            "purchase_id": purchase.id,
            "amount_naira": kobo_to_naira(amount_kobo),
            "provider_response": body
        }, "Airtime successful")

    # =====================================================
    # ELECTRICITY BILL PAYMENT
    # =====================================================
    @bp.post("/electricity/pay")
    @auth_required
    def electricity_pay_route():
        user = request.user
        data = request.get_json(force=True)

        disco = data.get("disco")
        meter = data.get("meter_number")
        meter_type = data.get("meter_type")
        amount = data.get("amount")
        phone = data.get("phone")

        if not disco or not meter or not meter_type or not amount:
            return error_response("disco, meter_number, meter_type, amount required")

        provider_code = f"{disco}_{meter_type}_{amount}"
        price = get_price_or_fail("ELECTRICITY", provider_code)
        if not price:
            return error_response("Electricity tariff not available", 400)

        amount_kobo = price.selling_price_kobo()

        payload = {
            "disco": disco,
            "meter_number": meter,
            "meter_type": meter_type,
            "amount": amount,
            "phone": phone,
            "reference": uid("ref_")
        }

        purchase = _create_purchase(user, "ELECTRICITY", amount_kobo, payload)
        debit, err = _debit_wallet(user, amount_kobo, "Electricity bill")
        if err:
            purchase.status = "FAILED"
            db.session.commit()
            return err

        status, body = buy_bill_payment(payload)
        purchase.response_payload = body

        if status not in (200, 201):
            purchase.status = "FAILED"
            db.session.commit()
            _refund_wallet(user, amount_kobo, "Refund: Electricity failed")
            return error_response("Electricity payment failed", 502, {"provider": body})

        purchase.status = "SUCCESS"
        db.session.commit()

        return success_response({
            "purchase_id": purchase.id,
            "amount_naira": kobo_to_naira(amount_kobo),
            "provider_response": body
        }, "Electricity paid")

    # =====================================================
    # CABLE SUBSCRIPTION
    # =====================================================
    @bp.post("/cable/subscribe")
    @auth_required
    def cable_subscribe_route():
        user = request.user
        data = request.get_json(force=True)

        cable = data.get("cable_name")
        iuc = data.get("smart_card_number")
        package = data.get("package")
        amount = data.get("amount")
        phone = data.get("phone")

        if not cable or not iuc or not package or not amount:
            return error_response("cable_name, smart_card_number, package, amount required")

        provider_code = f"{cable}_{package}"
        price = get_price_or_fail("CABLE", provider_code)
        if not price:
            return error_response("Cable package not available", 400)

        amount_kobo = price.selling_price_kobo()

        payload = {
            "cable_name": cable,
            "smart_card_number": iuc,
            "package": package,
            "amount": amount,
            "phone": phone,
            "reference": uid("ref_")
        }

        purchase = _create_purchase(user, "CABLE", amount_kobo, payload)
        debit, err = _debit_wallet(user, amount_kobo, "Cable subscription")
        if err:
            purchase.status = "FAILED"
            db.session.commit()
            return err

        status, body = buy_cable_subscription(payload)
        purchase.response_payload = body

        if status not in (200, 201):
            purchase.status = "FAILED"
            db.session.commit()
            _refund_wallet(user, amount_kobo, "Refund: Cable failed")
            return error_response("Cable subscription failed", 502, {"provider": body})

        purchase.status = "SUCCESS"
        db.session.commit()

        return success_response({
            "purchase_id": purchase.id,
            "amount_naira": kobo_to_naira(amount_kobo),
            "provider_response": body
        }, "Cable subscription successful")

    # =====================================================
    # AIRTIME PIN
    # =====================================================
    @bp.post("/airtime/pin")
    @auth_required
    def airtime_pin_route():
        user = request.user
        data = request.get_json(force=True)

        network = data.get("network")
        network_amount = data.get("network_amount")
        quantity = data.get("quantity")
        name_on_card = data.get("name_on_card")

        if not network or not network_amount or not quantity or not name_on_card:
            return error_response("network, network_amount, quantity, name_on_card required")

        provider_code = f"{network}_{network_amount}"
        price = get_price_or_fail("AIRTIME_PIN", provider_code)
        if not price:
            return error_response("Airtime PIN price not available", 400)

        amount_kobo = price.selling_price_kobo() * int(quantity)

        payload = {
            "network": int(network),
            "network_amount": int(network_amount),
            "quantity": int(quantity),
            "name_on_card": name_on_card
        }

        purchase = _create_purchase(user, "AIRTIME_PIN", amount_kobo, payload)
        debit, err = _debit_wallet(user, amount_kobo, "Airtime PIN")
        if err:
            purchase.status = "FAILED"
            db.session.commit()
            return err

        status, body = generate_airtime_pin(**payload)
        purchase.response_payload = body

        if status not in (200, 201):
            purchase.status = "FAILED"
            db.session.commit()
            _refund_wallet(user, amount_kobo, "Refund: Airtime PIN failed")
            return error_response("Airtime PIN failed", 502, {"provider": body})

        purchase.status = "SUCCESS"
        db.session.commit()

        return success_response({
            "purchase_id": purchase.id,
            "amount_naira": kobo_to_naira(amount_kobo),
            "provider_response": body
        }, "Airtime PIN generated")

    # =====================================================
    # EDUCATION PIN
    # =====================================================
    @bp.post("/education/epin")
    @auth_required
    def epin_route():
        user = request.user
        data = request.get_json(force=True)

        exam = data.get("exam_name")
        quantity = data.get("quantity")

        if not exam or not quantity:
            return error_response("exam_name, quantity required")

        provider_code = exam
        price = get_price_or_fail("EPIN", provider_code)
        if not price:
            return error_response("EPIN not available", 400)

        amount_kobo = price.selling_price_kobo() * int(quantity)

        payload = {
            "exam_name": exam,
            "quantity": int(quantity)
        }

        purchase = _create_purchase(user, "EPIN", amount_kobo, payload)
        debit, err = _debit_wallet(user, amount_kobo, "Education PIN")
        if err:
            purchase.status = "FAILED"
            db.session.commit()
            return err

        status, body = generate_epin(**payload)
        purchase.response_payload = body

        if status not in (200, 201):
            purchase.status = "FAILED"
            db.session.commit()
            _refund_wallet(user, amount_kobo, "Refund: EPIN failed")
            return error_response("EPIN failed", 502, {"provider": body})

        purchase.status = "SUCCESS"
        db.session.commit()

        return success_response({
            "purchase_id": purchase.id,
            "amount_naira": kobo_to_naira(amount_kobo),
            "provider_response": body
        }, "EPIN generated")
