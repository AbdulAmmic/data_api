import json
from flask import request
from models import db, ServicePurchase, WalletTransaction, PriceItem
from utils.responses import success_response, error_response
from utils.security import auth_required
from utils.helpers import uid, kobo_to_naira, naira_to_kobo
from utils.pricing import get_price_or_fail
from utils.bilalsadasub import (
    buy_data,
    buy_airtime_topup,
    buy_bill_payment,
    buy_cable_subscription,
    validate_meter,
    validate_iuc,
    generate_airtime_pin,
    generate_epin
)
from plans.electricity_plans import get_disco

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
            provider="BILALSADASUB",
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
            provider="BILALSADASUB",
            request_payload=json.dumps(payload)
        )
        db.session.add(purchase)
        db.session.commit()
        return purchase

    def _safe_json(body):
        """Safely parse JSON from provider body."""
        if not body: return {}
        try:
            return json.loads(body)
        except:
            return {"raw_response": body}



    # =====================================================
    # PLANS LINKED TO CONFIG
    # =====================================================
    # =====================================================
    # PLANS LINKED TO CONFIG (JSON RELOAD)
    # =====================================================
    import os
    
    def load_json_plans(filename):
        try:
            path = os.path.join(os.getcwd(), "plans", filename)
            if not os.path.exists(path): return []
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return []

    # helpers for lookups
    def get_price_item(item_id):
        return db.session.get(PriceItem, item_id)

    @bp.get("/plans")
    def get_plans():
        service_type = request.args.get("service") # DATA, CABLE, EPIN
        
        if service_type == "DATA":
            plans = PriceItem.query.filter_by(service="DATA", is_active=True).all()
            data = []
            for p in plans:
                data.append({
                    "id": p.id,
                    "service": "DATA",
                    "amount": p.selling_price_kobo() / 100,
                    "name": p.name,
                    "network": p.network,
                    "plan_type": p.plan_type,
                    "size": "", # size is included in name now
                    "validity": p.validity
                })
            return success_response(data)

        elif service_type == "CABLE":
            plans = PriceItem.query.filter_by(service="CABLE", is_active=True).all()
            data = []
            cable_map = {"gotv": "1", "dstv": "2", "startimes": "3"}
            for p in plans:
                data.append({
                    "id": p.id,
                    "service": "CABLE",
                    "amount": p.selling_price_kobo() / 100,
                    "name": p.name,
                    "cable_provider": cable_map.get(str(p.network).lower(), "1")
                })
            return success_response(data)

        elif service_type == "EPIN":
            plans = PriceItem.query.filter_by(service="EPIN", is_active=True).all()
            data = []
            for p in plans:
                data.append({
                    "id": p.id,
                    "service": "EPIN",
                    "amount": p.selling_price_kobo() / 100,
                    "name": p.name
                })
            return success_response(data)
            
        elif service_type == "ELECTRICITY":
            plans = PriceItem.query.filter_by(service="ELECTRICITY", is_active=True).all()
            data = []
            for p in plans:
                data.append({
                    "id": p.id,
                    "service": "ELECTRICITY",
                    "name": p.name,
                    "disco_id": p.provider_code
                })
            return success_response(data)

        return success_response([])

    # =====================================================
    # VALIDATIONS (FREE)
    # =====================================================
    @bp.get("/validate/meter")
    @auth_required
    def validate_meter_route():
        meter = request.args.get("meternumber")
        disco = request.args.get("disconame") # We might receive config ID e.g. 'ikeja-electric'
        mtype = request.args.get("mtype")

        if not meter or not disco:
            return error_response("meternumber, disconame, mtype required")
        
        # Resolve disco if it's our DB ID
        plan_item = get_price_item(disco)
        provider_disco_id = plan_item.provider_code if plan_item else disco

        status, body = validate_meter(meter, provider_disco_id, mtype or "prepaid")
        parsed_body = _safe_json(body)
        if status != 200:
            return error_response("Meter validation failed", 502, {"provider": parsed_body})

        return success_response({"provider_response": parsed_body})

    @bp.get("/validate/iuc")
    @auth_required
    def validate_iuc_route():
        iuc = request.args.get("smart_card_number")
        cable = request.args.get("cablename") # e.g. 'gotv-package-id'

        if not iuc or not cable:
            return error_response("smart_card_number, cablename required")

        # Resolve cable from DB
        plan_item = get_price_item(cable)
        if plan_item:
            # Map cable name to Bilal ID
            cable_map = {"gotv": 1, "dstv": 2, "startimes": 3}
            cable_id = cable_map.get(str(plan_item.network).lower(), 1)
        else:
            cable_id = 1

        status, body = validate_iuc(iuc, cable_id)
        parsed_body = _safe_json(body)
        if status != 200:
            return error_response("IUC validation failed", 502, {"provider": parsed_body})

        return success_response({"provider_response": parsed_body})

    # =====================================================
    # DATA PURCHASE (CONFIG BASED)
    # =====================================================
    # ... (Buy Data Route - Already Updated) ...

    # =====================================================
    # AIRTIME (Standard)
    # =====================================================
    @bp.post("/airtime/buy")
    @auth_required
    def buy_airtime_route():
        user = request.user
        data = request.get_json(force=True)
        
        network = data.get("network")
        amount = data.get("amount") # Naira
        phone = data.get("phone")
        
        if not network or not amount or not phone:
             return error_response("network, amount, phone required")

        transaction_pin = data.get("transaction_pin")
        if not user.check_pin(transaction_pin):
            return error_response("Invalid Transaction PIN", 403)

        # Bilalsadasub Network IDs: MTN=1, AIRTEL=2, GLO=3, 9MOBILE=4
        net_map = {"mtn": 1, "airtel": 2, "glo": 3, "9mobile": 4}
        try:
            net_id = int(network)
        except (ValueError, TypeError):
            net_id = net_map.get(str(network).lower(), 1)

        amount_kobo = naira_to_kobo(float(amount))
        
        payload = {
            "network": net_id,
            "amount": int(float(amount)),
            "phone": phone,
            "plan_type": "VTU",
            "request-id": uid("ref_")
        }

        purchase = _create_purchase(user, "AIRTIME", amount_kobo, payload)
        debit, err = _debit_wallet(user, amount_kobo, "Airtime purchase")
        if err:
             purchase.status = "FAILED"
             db.session.commit()
             return err

        status, body = buy_airtime_topup(payload)
        parsed_body = _safe_json(body)
        purchase.response_payload = body # Store raw for history
        if status not in (200, 201):
            purchase.status = "FAILED"
            db.session.commit()
            _refund_wallet(user, amount_kobo, "Refund: Airtime failed")
            p_msg = parsed_body.get("response") or parsed_body.get("message") or "Airtime failed"
            return error_response(p_msg, 502, {"provider": parsed_body})

        purchase.status = "SUCCESS"
        db.session.commit()
        return success_response({
            "purchase_id": purchase.id,
            "provider_response": parsed_body
        }, "Airtime successful")


    # =====================================================
    # ELECTRICITY (CONFIG BASED)
    # =====================================================
    @bp.post("/electricity/pay")
    @auth_required
    def electricity_pay_route():
        user = request.user
        data = request.get_json(force=True)
        
        disco_id = data.get("disco") # e.g. "ikeja-electric"
        meter = data.get("meter")
        mtype = data.get("mtype") # prepaid
        amount = data.get("amount") # Naira
        
        if not disco_id or not meter or not amount:
            return error_response("disco, meter, amount required")

        transaction_pin = data.get("transaction_pin")
        if not user.check_pin(transaction_pin):
            return error_response("Invalid Transaction PIN", 403)
            
        # disco_id is now the DB ID from PriceItem
        plan_item = get_price_item(disco_id)
        if not plan_item:
            return error_response("Invalid Disco selected", 400)
            
        amount_kobo = naira_to_kobo(float(amount))
        amount_naira = float(amount)

        payload = {
            "disco": int(plan_item.provider_code), # Bilal Disco ID
            "amount": int(float(amount)),
            "meter_number": meter, 
            "meter_type": (mtype or "prepaid").lower(),
            "request-id": uid("ref_")
        }

        purchase = _create_purchase(user, "ELECTRICITY", amount_kobo, payload)
        debit, err = _debit_wallet(user, amount_kobo, "Electricity Bill")
        if err:
            purchase.status = "FAILED"; db.session.commit(); return err

        status, body = buy_bill_payment(payload)
        purchase.response_payload = body
        
        parsed_body = _safe_json(body)

        if status not in (200, 201):
             purchase.status = "FAILED"; db.session.commit()
             _refund_wallet(user, amount_kobo, "Refund: Electricity failed")
             p_msg = parsed_body.get("response") or parsed_body.get("message") or "Payment failed"
             return error_response(p_msg, 502, {"provider": parsed_body})

        purchase.status = "SUCCESS"; db.session.commit()
        return success_response({
            "purchase_id": purchase.id,
            "provider_response": parsed_body
        }, "Payment successful")


    # =====================================================
    # CABLE TV (CONFIG BASED)
    # =====================================================
    @bp.post("/cable/subscribe")
    @auth_required
    def cable_subscribe_route():
        user = request.user
        data = request.get_json(force=True)
        
        plan_id = data.get("plan") # e.g. "gotv-max"
        iuc = data.get("iuc")
        
        if not plan_id or not iuc:
            return error_response("plan, iuc required")

        transaction_pin = data.get("transaction_pin")
        if not user.check_pin(transaction_pin):
            return error_response("Invalid Transaction PIN", 403)

        # plan_id is now the DB ID from PriceItem
        plan_item = get_price_item(plan_id)
        if not plan_item:
             return error_response("Invalid Cable Plan selected", 400)

        amount_kobo = plan_item.selling_price_kobo()
        amount_naira = amount_kobo / 100

        # Bilal Cable IDs: GOTV=1, DSTV=2, STARTIMES=3
        cable_map = {"gotv": 1, "dstv": 2, "startimes": 3}
        cable_id = cable_map.get(str(plan_item.network).lower(), 1)

        payload = {
            "cable": cable_id,
            "cable_plan": int(plan_item.provider_code), # Bilal Plan ID
            "iuc": iuc,
            "request-id": uid("ref_")
        }

        purchase = _create_purchase(user, "CABLE", amount_kobo, payload)
        debit, err = _debit_wallet(user, amount_kobo, "Cable Subscription")
        if err:
            purchase.status = "FAILED"; db.session.commit(); return err

        status, body = buy_cable_subscription(payload)
        parsed_body = _safe_json(body)
        purchase.response_payload = body

        if status not in (200, 201):
             purchase.status = "FAILED"; db.session.commit()
             _refund_wallet(user, amount_kobo, "Refund: Cable failed")
             p_msg = parsed_body.get("response") or parsed_body.get("message") or "Subscription failed"
             return error_response(p_msg, 502, {"provider": parsed_body})

        purchase.status = "SUCCESS"; db.session.commit()
        return success_response({
            "purchase_id": purchase.id,
            "provider_response": parsed_body
        }, "Subscription successful")


    # =====================================================
    # EDUCATION PIN (CONFIG BASED)
    # =====================================================
    @bp.post("/education/epin")
    @auth_required
    def epin_route():
        user = request.user
        data = request.get_json(force=True)
        
        exam_id = data.get("exam_type") # e.g. "waec"
        quantity = data.get("quantity", 1)
        
        if not exam_id: return error_response("exam_type required")

        transaction_pin = data.get("transaction_pin")
        if not user.check_pin(transaction_pin):
            return error_response("Invalid Transaction PIN", 403)

        # exam_id is now the DB ID from PriceItem
        plan_item = get_price_item(exam_id)
        if not plan_item:
             return error_response("Invalid Exam Type selected", 400)

        amount_kobo = plan_item.selling_price_kobo() * int(quantity)
        amount_naira = amount_kobo / 100

        payload = {
            "exam": int(plan_item.provider_code), # Bilal Exam ID
            "quantity": int(quantity),
            "request-id": uid("ref_")
        }
        
        # If provider doesn't support bulk, we might need loop. 
        # Assuming provider supports single check mostly. 
        # Postman docs usually say "quantity" or check if it's 1 by 1.
        # Assuming 1 for now or provider handles it.

        purchase = _create_purchase(user, "EPIN", amount_kobo, payload)
        debit, err = _debit_wallet(user, amount_kobo, "Education PIN")
        if err:
             purchase.status = "FAILED"; db.session.commit(); return err
        
        status, body = generate_epin(payload)
        parsed_body = _safe_json(body)

        purchase.response_payload = body
        
        if status not in (200, 201):
             purchase.status = "FAILED"; db.session.commit()
             _refund_wallet(user, amount_kobo, "Refund: PIN Generation failed")
             p_msg = parsed_body.get("response") or parsed_body.get("message") or "PIN Generation failed"
             return error_response(p_msg, 502, {"provider": parsed_body})
        
        purchase.status = "SUCCESS"; db.session.commit()
        return success_response({
            "purchase_id": purchase.id,
            "provider_response": parsed_body
        }, "PIN generated")

    # =====================================================
    # DATA PURCHASE (CONFIG BASED)
    # =====================================================
    @bp.post("/data/buy")
    @auth_required
    def buy_data_route():
        user = request.user
        data = request.get_json(force=True)

        network = data.get("network") # e.g. "mtn"
        plan_id = data.get("plan")    # e.g. "sme-data-1-xxx" (frontend strips 'mtn-')
        phone = data.get("phone")

        if not network or not plan_id or not phone:
            return error_response("network, plan, phone required")

        # Try searching by exact ID, if not found, try prepending network
        plan_item = get_price_item(plan_id)
        if not plan_item:
            alt_id = f"{network.lower()}-{plan_id}"
            plan_item = get_price_item(alt_id)
            
        if not plan_item:
             return error_response(f"Data plan not found: {plan_id}", 400)

        transaction_pin = data.get("transaction_pin")
        if not user.check_pin(transaction_pin):
            return error_response("Invalid Transaction PIN", 403)

        # Price in Naira from DB -> Already includes 5% markup via model logic
        amount_kobo = plan_item.selling_price_kobo()
        amount_naira = amount_kobo / 100

        # Bilalsadasub Network IDs: MTN=1, AIRTEL=2, GLO=3, 9MOBILE=4
        net_map = {"mtn": 1, "airtel": 2, "glo": 3, "9mobile": 4}
        
        # Determine network ID from plan_item or fallback to request param
        target_network = (plan_item.network or network).lower()
        net_id = net_map.get(target_network, 1)

        payload = {
            "network": net_id,
            "data_plan": int(plan_item.provider_code), # Bilal Plan ID
            "phone": phone,
            "bypass": False,
            "request-id": uid("ref_")
        }

        purchase = _create_purchase(user, "DATA", amount_kobo, payload)
        debit, err = _debit_wallet(user, amount_kobo, "Data purchase")
        if err:
            purchase.status = "FAILED"
            db.session.commit()
            return err

        status, body = buy_data(payload)
        parsed_body = _safe_json(body)
        purchase.response_payload = body

        # Check for HTTP errors or logical errors in the JSON response
        is_success = (status in (200, 201)) and (str(parsed_body.get("status", "")).lower() == "success")

        if not is_success:
            purchase.status = "FAILED"
            db.session.commit()
            _refund_wallet(user, amount_kobo, "Refund: Data failed")
            p_msg = parsed_body.get("response") or parsed_body.get("message") or "Purchase failed"
            return error_response(p_msg, 502, {"provider": parsed_body})

        purchase.status = "SUCCESS"
        db.session.commit()

        return success_response({
            "purchase_id": purchase.id,
            "amount_naira": amount_naira,
            "provider_response": parsed_body
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

        transaction_pin = data.get("transaction_pin")
        if not user.check_pin(transaction_pin):
            return error_response("Invalid Transaction PIN", 403)

        provider_code = f"{network}_{amount}"
        price = get_price_or_fail("AIRTIME", provider_code)
        
        # Fallback to network-based plan
        if not price:
            price = PriceItem.query.filter_by(service="AIRTIME", network=network, is_active=True).first()

        if not price:
            return error_response(f"Airtime for {network} not available", 400)

        # If it's a specific price item (fixed amount), use its selling price
        if price.provider_code == provider_code:
            amount_kobo = price.selling_price_kobo()
        else:
            # Dynamic amount (face value)
            # We could implement a percentage markup/discount here if needed using price.markup_value
            # For now, we assume selling at face value
            amount_kobo = naira_to_kobo(float(amount))

        # Bilalsadasub Network IDs: MTN=1, AIRTEL=2, GLO=3, 9MOBILE=4
        net_map = {"mtn": 1, "airtel": 2, "glo": 3, "9mobile": 4}
        try:
            net_id = int(network)
        except (ValueError, TypeError):
            net_id = net_map.get(str(network).lower(), 1)

        payload = {
            "network": net_id,
            "amount": int(float(amount)),
            "phone": phone,
            "plan_type": "VTU",
            "request-id": uid("ref_")
        }

        purchase = _create_purchase(user, "AIRTIME", amount_kobo, payload)
        debit, err = _debit_wallet(user, amount_kobo, "Airtime topup")
        if err:
            purchase.status = "FAILED"
            db.session.commit()
            return err

        status, body = buy_airtime_topup(payload)
        parsed_body = _safe_json(body)
        purchase.response_payload = body

        # Check for HTTP errors or logical errors in the JSON response
        is_success = (status in (200, 201)) and (str(parsed_body.get("status", "")).lower() == "success")

        if not is_success:
            purchase.status = "FAILED"
            db.session.commit()
            _refund_wallet(user, amount_kobo, "Refund: Airtime failed")
            return error_response("Airtime failed", 502, {"provider": parsed_body})

        purchase.status = "SUCCESS"
        db.session.commit()

        return success_response({
            "purchase_id": purchase.id,
            "amount_naira": kobo_to_naira(amount_kobo),
            "provider_response": parsed_body
        }, "Airtime successful")



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

        transaction_pin = data.get("transaction_pin")
        if not user.check_pin(transaction_pin):
            return error_response("Invalid Transaction PIN", 403)

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

        # Map keys for Bilalsadasub Recharge Card API
        status, body = generate_airtime_pin(
            network=int(network),
            plan_type=int(price.provider_code), # Use the specific Bilal Plan ID
            quantity=int(quantity),
            card_name=name_on_card
        )
        parsed_body = _safe_json(body)
        purchase.response_payload = body

        if status not in (200, 201):
            purchase.status = "FAILED"
            db.session.commit()
            _refund_wallet(user, amount_kobo, "Refund: Airtime PIN failed")
            return error_response("Airtime PIN failed", 502, {"provider": parsed_body})

        purchase.status = "SUCCESS"
        db.session.commit()

        return success_response({
            "purchase_id": purchase.id,
            "amount_naira": kobo_to_naira(amount_kobo),
            "provider_response": parsed_body
        }, "Airtime PIN generated")



    # =====================================================
    # AIRTIME TO CASH
    # =====================================================
    @bp.post("/airtime/cash")
    @auth_required
    def airtime_to_cash_route():
        from models import AirtimeToCashTransaction
        from utils.cheetahpay import CheetahPayClient
        user = request.user
        data = request.get_json(force=True)

        network = data.get("network")
        phone_from = data.get("phone_from")
        amount = data.get("amount")
        share_pin = data.get("share_pin") # This could be the card PIN or the transfer PIN
        transaction_pin = data.get("transaction_pin")

        if not network or not phone_from or not amount:
            return error_response("network, phone_from, amount required")

        if not user.check_pin(transaction_pin):
            return error_response("Invalid Transaction PIN", 403)

        try:
            amount_naira = float(amount)
        except:
            return error_response("Invalid amount format", 400)

        tx_id = uid("a2c_")
        
        # Initialize Cheetahpay Client
        client = CheetahPayClient()
        
        # Determine if it's a PIN or a Transfer
        # If share_pin looks like a 10-16 digit recharge pin, we treat as PIN deposit.
        # Otherwise, we treat it as a Transfer deposit.
        is_pin_deposit = share_pin and len(share_pin) >= 10 and share_pin.isdigit()
        
        if is_pin_deposit:
             status_code, response = client.deposit_airtime_pin(
                 pin=share_pin,
                 amount=amount_naira,
                 network=network,
                 order_id=tx_id
             )
        else:
             status_code, response = client.initiate_airtime_transfer(
                 amount=amount_naira,
                 network=network,
                 depositor_phone=phone_from,
                 order_id=tx_id
             )

        # Log Cheetahpay response
        print(f"Cheetahpay Response ({tx_id}): {response}")

        # Note: Even if Cheetahpay fails initially, we might want to record it
        # or just return error to user.
        if status_code not in [200, 201] or not response.get("success"):
             return error_response(f"Cheetahpay Error: {response.get('message', 'Failed to initiate')}", status_code)

        tx = AirtimeToCashTransaction(
            id=tx_id,
            user_id=user.id,
            network=network,
            phone_from=phone_from,
            amount_sent=int(amount_naira),
            amount_kobo=naira_to_kobo(amount_naira),
            share_pin=share_pin,
            status="PENDING",
            provider_reference=response.get("reference") or response.get("transaction_id")
        )
        
        db.session.add(tx)
        db.session.commit()

        return success_response({
            "id": tx.id,
            "status": "PENDING",
            "message": response.get("message", "Request submitted successfully. Waiting for Cheetahpay confirmation."),
            "cheetahpay_response": response
        })

    # =====================================================
    # TRANSACTION HISTORY & RECEIPT
    # =====================================================
    @bp.get("/history")
    @auth_required
    def list_service_history():
        """
        List all service purchases (Data, Airtime, Cable, etc.)
        """
        user = request.user
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)

        pagination = (
            ServicePurchase.query
            .filter_by(user_id=user.id)
            .order_by(ServicePurchase.created_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

        items = []
        for p in pagination.items:
            # Parse payloads safely to get details like "phone", "plan"
            details = {}
            try:
                # 1. Start with request (contains user input: phone, amount, network)
                if p.request_payload:
                    details.update(json.loads(p.request_payload))
                
                # 2. Update with response (contains success status, tokens, refs)
                if p.response_payload:
                    details.update(json.loads(p.response_payload))
            except:
                pass

            items.append({
                "id": p.id,
                "service": p.service,
                "amount": kobo_to_naira(p.amount_kobo),
                "status": p.status,
                "date": p.created_at.isoformat(),
                "details": details
            })

        return success_response({
            "items": items,
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": pagination.page
        })

    @bp.get("/transaction/<id>")
    @auth_required
    def get_transaction_details(id):
        """
        Get full details for a receipt
        """
        user = request.user
        tx = ServicePurchase.query.filter_by(id=id, user_id=user.id).first()
        
        if not tx:
            return error_response("Transaction not found", 404)

        data = {
            "id": tx.id,
            "service": tx.service,
            "amount": kobo_to_naira(tx.amount_kobo),
            "status": tx.status,
            "date": tx.created_at.isoformat(),
            "provider": tx.provider,
        }

        # Embed payloads
        try:
            if tx.request_payload:
                data["request"] = json.loads(tx.request_payload)
            if tx.response_payload:
                data["response"] = json.loads(tx.response_payload)
        except:
            pass

        return success_response(data)
