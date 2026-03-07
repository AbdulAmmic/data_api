import json
from flask import request
from models import db, ServicePurchase, WalletTransaction, PriceItem
from utils.responses import success_response, error_response
from utils.security import auth_required
from utils.helpers import uid, kobo_to_naira, naira_to_kobo
from utils.pricing import get_price_or_fail
from utils.peyflex import (
    buy_data,
    buy_airtime_topup,
    buy_bill_payment,
    buy_cable_subscription,
    validate_meter,
    validate_iuc
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
            provider="PEYFLEX",
            reference=uid("pf_")
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
            provider="PEYFLEX",
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

    DATA_PLANS = load_json_plans("data_plans.json")
    CABLE_PLANS = load_json_plans("cable_plans.json")
    
    # Helpers for lookups
    def get_plan_by_id(plan_id):
        # Reloading here if we want dynamic updates without restart? 
        # For performance, maybe better to load once. User wants "simple".
        # Let's check if we should reload every time or just use the variable.
        # User said "then me use them", implying they edit and it works.
        # So reload might be better in the function, but for now lets keep global load at route reg time or inside route?
        # If I put it inside register_service_routes, it runs once at startup basically.
        # Let's move loading INSIDE the routes or a getter helper to allow hot-updates.
        return next((p for p in DATA_PLANS if p["id"] == plan_id), None)

    def get_cable_plan(plan_id):
        return next((p for p in CABLE_PLANS if p["id"] == plan_id), None)

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
                    "plan_type": p["type"],
                    "size": p.get("size", ""),
                    "validity": p.get("validity", "")
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
        parsed_body = _safe_json(body)
        if status != 200:
            return error_response("Meter validation failed", 502, {"provider": parsed_body})

        return success_response({"provider_response": parsed_body})

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

        # Config map for Network IDs? 
        # MTN=1, GLO=2, 9MOBILE=3, AIRTEL=4? 
        # Or Just send String? DataStation docs say ID.
        net_map = {"mtn": "1", "glo": "2", "9mobile": "3", "airtel": "4"}
        net_id = net_map.get(network.lower(), network)

        amount_kobo = naira_to_kobo(float(amount))
        
        payload = {
            "network": net_id,
            "amount": amount,
            "mobile_number": phone
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
            return error_response("Airtime failed", 502, {"provider": parsed_body})

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
            
        disco_conf = get_disco(disco_id)
        if not disco_conf:
            return error_response("Invalid Disco ID", 400)
            
        amount_kobo = naira_to_kobo(float(amount))
        
        m_type_val = "postpaid" if (mtype or "prepaid").lower() == "postpaid" else "prepaid"

        payload = {
            "identifier": "electricity",
            "plan": disco_id,
            "amount": amount,
            "meter": meter, 
            "type": m_type_val,
            "phone": "08000000000" # default if user phone is missing on electricity
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
             return error_response("Payment failed", 502, {"provider": parsed_body})

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

        plan_conf = get_cable_plan(plan_id)
        if not plan_conf:
             return error_response("Invalid Cable Plan", 400)

        # Selling Price = amount (from config it's selling price)
        amount_naira = plan_conf["amount"]
        amount_kobo = naira_to_kobo(amount_naira)

        payload = {
            "identifier": plan_conf["cable_id"], # e.g., 'gotv', 'dstv'
            "plan": plan_conf["package_id"],     # e.g., 'max', 'yanga'
            "iuc": iuc,
            "amount": amount_naira,
            "phone": "08000000000"
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
             return error_response("Subscription failed", 502, {"provider": parsed_body})

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
        return error_response("EPIN is currently not supported by the new provider.", 400)

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

        # The frontend now dynamically queries Peyflex for plans and sends exact Peyflex network & plan codes.
        # e.g., network='mtn_gifting_data', plan='M500MBS'
        # We bypass strict config plan_id lookups because Peyflex codes change dynamically.
        amount = data.get("amount") # Add amount to payload from frontend since we bypass DB lookups for prices

        if not amount:
            return error_response("amount is required", 400)
            
        transaction_pin = data.get("transaction_pin")
        if not user.check_pin(transaction_pin):
            return error_response("Invalid Transaction PIN", 403)

        # Price in Naira from frontend -> Convert to Kobo
        try:
             amount_naira = float(amount)
        except:
             return error_response("Invalid amount", 400)
        amount_kobo = naira_to_kobo(amount_naira)

        payload = {
            "network": network, 
            "plan_code": plan_id,  
            "mobile_number": phone
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

        if status not in (200, 201):
            purchase.status = "FAILED"
            db.session.commit()
            _refund_wallet(user, amount_kobo, "Refund: Data failed")
            return error_response("Data purchase failed", 502, {"provider": parsed_body})

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
        
        # Fallback to generic network pricing
        if not price:
            price = get_price_or_fail("AIRTIME", network)

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

        # Map network to ID
        net_map = {"mtn": "1", "glo": "2", "9mobile": "3", "airtel": "4"}
        net_id = net_map.get(network.lower(), network)

        payload = {
            "network": net_id,
            "amount": amount,
            "mobile_number": phone,
            "Ported_number": True,
            "airtime_type": "VTU"
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

        if status not in (200, 201):
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
         return error_response("Airtime PIN is currently not supported by the new provider.", 400)



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
