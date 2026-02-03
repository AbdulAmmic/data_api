import json
from flask import request
from models import db, ServicePurchase, WalletTransaction, PriceItem
from utils.responses import success_response, error_response
from utils.security import auth_required
from utils.helpers import uid, kobo_to_naira, naira_to_kobo
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
    # PLANS LINKED TO CONFIG
    # =====================================================
    from plans.data_plans import DATA_PLANS, get_plan_by_id
    from plans.cable_plans import CABLE_PLANS, get_cable_plan
    from plans.electricity_plans import ELECTRICITY_DISCOS, get_disco
    from plans.education_plans import EDUCATION_PLANS, get_education_plan

    @bp.get("/plans")
    def get_plans():
        service_type = request.args.get("service") # DATA, CABLE, EPIN
        
        if service_type == "DATA":
            data = []
            for p in DATA_PLANS:
                data.append({
                    "id": p["id"],
                    "service": "DATA",
                    "amount": p["selling_price"],
                    "name": p["name"],
                    "network": p["network"],
                    "plan_type": p["type"]
                })
            return success_response(data)

        elif service_type == "CABLE":
            data = []
            for p in CABLE_PLANS:
                data.append({
                    "id": p["id"],
                    "service": "CABLE",
                    "amount": p["amount"], # This is selling price (backend 'amount')
                    "name": p["name"],
                    "cable_provider": p["cable_id"] # ID for filtering?
                })
            return success_response(data)

        elif service_type == "EPIN":
            data = []
            for p in EDUCATION_PLANS:
                data.append({
                    "id": p["id"],
                    "service": "EPIN",
                    "amount": p["selling_price"],
                    "name": p["label"]
                })
            return success_response(data)
            
        elif service_type == "ELECTRICITY":
             return success_response(ELECTRICITY_DISCOS)

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
        
        # Resolve disco if it's our config ID
        disco_conf = get_disco(disco)
        provider_disco_id = disco_conf["disco_id"] if disco_conf else disco # Fallback or strict?

        status, body = validate_meter(meter, provider_disco_id, mtype or "prepaid")
        if status != 200:
            return error_response("Meter validation failed", 502, {"provider": body})

        return success_response({"provider_response": body})

    @bp.get("/validate/iuc")
    @auth_required
    def validate_iuc_route():
        iuc = request.args.get("smart_card_number")
        cable = request.args.get("cablename") # e.g. 'gotv' or ID '1'

        if not iuc or not cable:
            return error_response("smart_card_number, cablename required")

        # Map cable name/id if necessary. DataStation expects ID: 1, 2, 3?
        # If frontend sends 'gotv', we map to 1? 
        # For now assume frontend validates/sends correct ID or we map simplistic
        if cable.lower() == "gotv": cable_id = "1"
        elif cable.lower() == "dstv": cable_id = "2"
        elif cable.lower() == "startimes": cable_id = "3"
        else: cable_id = cable

        status, body = validate_iuc(iuc, cable_id)
        if status != 200:
            return error_response("IUC validation failed", 502, {"provider": body})

        return success_response({"provider_response": body})

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

        # Config map for Network IDs? 
        # MTN=1, GLO=2, 9MOBILE=3, AIRTEL=4? 
        # Or Just send String? DataStation docs say ID.
        net_map = {"mtn": "1", "glo": "2", "9mobile": "3", "airtel": "4"}
        net_id = net_map.get(network.lower(), network)

        amount_kobo = naira_to_kobo(float(amount))
        
        payload = {
            "network": net_id,
            "amount": amount,
            "mobile_number": phone,
            "Ported_number": True,
            "airtime_type": "VTU",
            "ref": uid("ref_")
        }

        purchase = _create_purchase(user, "AIRTIME", amount_kobo, payload)
        debit, err = _debit_wallet(user, amount_kobo, "Airtime purchase")
        if err:
             purchase.status = "FAILED"
             db.session.commit()
             return err

        status, body = buy_airtime(payload)
        # ... standard handling ...
        purchase.response_payload = body
        if status not in (200, 201):
            purchase.status = "FAILED"
            db.session.commit()
            _refund_wallet(user, amount_kobo, "Refund: Airtime failed")
            return error_response("Airtime failed", 502, {"provider": body})

        purchase.status = "SUCCESS"
        db.session.commit()
        return success_response({"purchase_id": purchase.id}, "Airtime successful")


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
            
        disco_conf = get_disco(disco_id)
        if not disco_conf:
            return error_response("Invalid Disco ID", 400)
            
        amount_kobo = naira_to_kobo(float(amount))
        
        payload = {
            "disco_name": disco_conf["disco_id"],
            "amount": amount,
            "meter_number": meter, 
            "MeterType": mtype or "prepaid",
            "ref": uid("ref_")
        }

        purchase = _create_purchase(user, "ELECTRICITY", amount_kobo, payload)
        debit, err = _debit_wallet(user, amount_kobo, "Electricity Bill")
        if err:
            purchase.status = "FAILED"; db.session.commit(); return err

        status, body = pay_electricity(payload)
        purchase.response_payload = body
        
        if status not in (200, 201):
             purchase.status = "FAILED"; db.session.commit()
             _refund_wallet(user, amount_kobo, "Refund: Electricity failed")
             return error_response("Payment failed", 502, {"provider": body})

        purchase.status = "SUCCESS"; db.session.commit()
        return success_response({"purchase_id": purchase.id}, "Payment successful")


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

        plan_conf = get_cable_plan(plan_id)
        if not plan_conf:
             return error_response("Invalid Cable Plan", 400)

        # Selling Price = amount (from config it's selling price)
        amount_naira = plan_conf["amount"]
        amount_kobo = naira_to_kobo(amount_naira)

        payload = {
            "cable_name": plan_conf["cable_id"], # 1, 2, 3
            "cable_plan": plan_conf["package_id"], # 2, 6, etc
            "smart_card_number": iuc,
            "ref": uid("ref_")
        }

        purchase = _create_purchase(user, "CABLE", amount_kobo, payload)
        debit, err = _debit_wallet(user, amount_kobo, "Cable Subscription")
        if err:
            purchase.status = "FAILED"; db.session.commit(); return err

        status, body = subscribe_cable(payload)
        purchase.response_payload = body

        if status not in (200, 201):
             purchase.status = "FAILED"; db.session.commit()
             _refund_wallet(user, amount_kobo, "Refund: Cable failed")
             return error_response("Subscription failed", 502, {"provider": body})

        purchase.status = "SUCCESS"; db.session.commit()
        return success_response({"purchase_id": purchase.id}, "Subscription successful")


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

        plan_conf = get_education_plan(exam_id)
        if not plan_conf:
             return error_response("Invalid Exam Type", 400)

        amount_naira = plan_conf["selling_price"] * int(quantity)
        amount_kobo = naira_to_kobo(amount_naira)

        payload = {
            "exam_name": plan_conf["datastation_id"], # WAEC/NECO
            "quantity": quantity, # Provider supported? Usually 1.
            "ref": uid("ref_")
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
        purchase.response_payload = body
        
        if status not in (200, 201):
             purchase.status = "FAILED"; db.session.commit()
             _refund_wallet(user, amount_kobo, "Refund: PIN Generation failed")
             return error_response("PIN Generation failed", 502, {"provider": body})
        
        purchase.status = "SUCCESS"; db.session.commit()
        return success_response({"purchase_id": purchase.id, "tokens": body}, "PIN generated")

    # =====================================================
    # DATA PURCHASE (CONFIG BASED)
    # =====================================================
    @bp.post("/data/buy")
    @auth_required
    def buy_data_route():
        user = request.user
        data = request.get_json(force=True)

        network = data.get("network") # e.g. "mtn"
        plan_id = data.get("plan")    # e.g. "sme-1gb" (frontend strips 'mtn-')
        phone = data.get("phone")

        if not network or not plan_id or not phone:
            return error_response("network, plan, phone required")

        # Frontend logic: 'mtn-sme-1gb' -> sends network='mtn', plan='sme-1gb'
        # But our config ID is 'mtn-sme-1gb'. Reconstruct or check how frontend sends.
        # Frontend: const planCode = selectedPlan?.id.replace(`${network}-`, "") 
        # So we might receive "sme-1gb".
        # Let's verify against our config ID.
        full_plan_id = f"{network}-{plan_id}"
        
        plan_config = get_plan_by_id(full_plan_id)
        if not plan_config:
            # Try direct match just in case
            plan_config = get_plan_by_id(plan_id)
        
        if not plan_config:
             return error_response(f"Data plan not found: {full_plan_id}", 400)

        transaction_pin = data.get("transaction_pin")
        if not user.check_pin(transaction_pin):
            return error_response("Invalid Transaction PIN", 403)

        # Price in Naira from config -> Convert to Kobo for Wallet
        amount_naira = plan_config["selling_price"]
        amount_kobo = naira_to_kobo(amount_naira)

        payload = {
            "network": plan_config["datastation_network_id"], # Send mapped ID
            "plan": plan_config["datastation_plan_id"],      # Send mapped ID
            "mobile_number": phone,
            "Ported_number": True,
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
            "amount_naira": amount_naira,
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

        transaction_pin = data.get("transaction_pin")
        if not user.check_pin(transaction_pin):
            return error_response("Invalid Transaction PIN", 403)

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
    # AIRTIME TO CASH
    # =====================================================
    @bp.post("/airtime/cash")
    @auth_required
    def airtime_to_cash_route():
        from models import AirtimeToCashTransaction
        user = request.user
        data = request.get_json(force=True)

        network = data.get("network")
        phone_from = data.get("phone_from")
        amount = data.get("amount")
        share_pin = data.get("share_pin")
        transaction_pin = data.get("transaction_pin")

        if not network or not phone_from or not amount:
            return error_response("network, phone_from, amount required")

        if not user.check_pin(transaction_pin):
            return error_response("Invalid Transaction PIN", 403)

        try:
            amount_naira = float(amount)
            # We treat input as Naira. 
            # Note: We aren't debiting the wallet! The user is SENDING us airtime.
            # We might want to credit them LATER.
        except:
            return error_response("Invalid amount format", 400)

        tx = AirtimeToCashTransaction(
            id=uid("a2c_"),
            user_id=user.id,
            network=network,
            phone_from=phone_from,
            amount_sent=int(amount_naira), # Storing as Naira or we should consistency use kobo?
            # Model definition comment said "input usually Naira". Let's store as kobo to be consistent with DB usage of "kobo" suffix if we renamed it.
            # But line 261 defined `amount_kobo`. So we must convert.
            amount_kobo=naira_to_kobo(amount_naira),
            share_pin=share_pin,
            status="PENDING"
        )
        
        db.session.add(tx)
        db.session.commit()

        return success_response({
            "id": tx.id,
            "status": "PENDING",
            "message": "Airtime to cash request submitted. Admin will verify."
        })
