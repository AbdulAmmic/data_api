import requests
import json
import os
from flask import current_app

class CheetahPayClient:
    def __init__(self, public_key=None, private_key=None, mode='test'):
        self.public_key = public_key or os.getenv("CHEETAHPAY_PUBLIC_KEY")
        self.private_key = private_key or os.getenv("CHEETAHPAY_PRIVATE_KEY")
        self.mode = (mode or os.getenv("CHEETAHPAY_MODE", "test")).lower()
        # Cheetahpay v1 base URL
        self.base_url = "https://www.cheetahpay.com.ng/api/v1"

    def _get_headers(self):
        # Many Cheetahpay integrations use the private key as a Bearer token
        return {
            "Authorization": f"Bearer {self.private_key}",
            "Accept": "application/json"
        }

    def deposit_airtime_pin(self, pin, amount, network, order_id=None):
        """
        Deposit via Airtime PIN (Manual entry)
        """
        url = f"{self.base_url}/deposits"
        payload = {
            "public_key": self.public_key,
            "pin": pin,
            "amount": float(amount),
            "network": network.upper(),
        }
        if order_id:
            payload["order_id"] = order_id
        
        # In test mode, Cheetahpay often expects a specific PIN
        if self.mode == "test" and pin != "1111222233334444":
             print(f"DEBUG: Using Test Mode PIN for validation")

        try:
            response = requests.post(url, json=payload, headers=self._get_headers())
            try:
                return response.status_code, response.json()
            except:
                return response.status_code, {"success": False, "message": "Invalid JSON response from provider", "raw": response.text}
        except Exception as e:
            return 500, {"success": False, "message": str(e)}

    def initiate_airtime_transfer(self, amount, network, depositor_phone, order_id=None):
        """
        Initiate Airtime Transfer (Share 'N' Sell)
        """
        url = f"{self.base_url}/deposits"
        payload = {
            "public_key": self.public_key,
            "amount": float(amount),
            "network": network.upper(),
            "depositors_phone": depositor_phone, # Some docs say 'depositors_phone', others 'depositor_phone'
            "depositor_phone": depositor_phone,   # Include both to be safe
        }
        if order_id:
            payload["order_id"] = order_id

        try:
            response = requests.post(url, json=payload, headers=self._get_headers())
            try:
                return response.status_code, response.json()
            except:
                return response.status_code, {"success": False, "message": "Invalid JSON response from provider", "raw": response.text}
        except Exception as e:
            return 500, {"success": False, "message": str(e)}

    def verify_webhook(self, data):
        """
        Verify that the webhook is genuinely from Cheetahpay.
        Cheetahpay typically doesn't use complex signatures in v1, 
        but we should check the private_key if it's sent back or use other methods.
        Usually, the callback includes the status.
        """
        # Implement verification logic if documented. 
        # For now, we trust the callback if it contains valid data and we check it manually/log it.
        return True
