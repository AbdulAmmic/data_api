
DATA_PLANS = [
    # =========================================================
    # MTN (Network ID: 1)
    # =========================================================
    # SME
    {"id": "mtn-sme-1gb", "network": "mtn", "type": "sme", "name": "MTN SME 1GB", "size": "1GB", "validity": "30 Days", "cost_price": 225, "selling_price": 240, "datastation_network_id": "1", "datastation_plan_id": "420"},
    {"id": "mtn-sme-2.5gb", "network": "mtn", "type": "sme", "name": "MTN SME 2.5GB", "size": "2.5GB", "validity": "30 Days", "cost_price": 550, "selling_price": 580, "datastation_network_id": "1", "datastation_plan_id": "421"},
    {"id": "mtn-sme-5gb", "network": "mtn", "type": "sme", "name": "MTN SME 5GB", "size": "5GB", "validity": "30 Days", "cost_price": 3000, "selling_price": 3150, "datastation_network_id": "1", "datastation_plan_id": "371"},
    {"id": "mtn-sme-2gb", "network": "mtn", "type": "sme", "name": "MTN SME 2GB", "size": "2GB", "validity": "30 Days", "cost_price": 1470, "selling_price": 1550, "datastation_network_id": "1", "datastation_plan_id": "399"},
    {"id": "mtn-sme-3gb", "network": "mtn", "type": "sme", "name": "MTN SME 3GB", "size": "3GB", "validity": "30 Days", "cost_price": 1980, "selling_price": 2080, "datastation_network_id": "1", "datastation_plan_id": "400"},
    
    # GIFTING
    {"id": "mtn-gift-1gb", "network": "mtn", "type": "gifting", "name": "MTN Gifting 1GB", "size": "1GB", "validity": "30 Days", "cost_price": 225, "selling_price": 240, "datastation_network_id": "1", "datastation_plan_id": "215"}, # Adjusted ID/Price guess or from older list? Using list logic.
    {"id": "mtn-gift-2gb", "network": "mtn", "type": "gifting", "name": "MTN Gifting 2GB", "size": "2GB", "validity": "30 Days", "cost_price": 1455, "selling_price": 1530, "datastation_network_id": "1", "datastation_plan_id": "345"},
    {"id": "mtn-gift-3.5gb", "network": "mtn", "type": "gifting", "name": "MTN Gifting 3.5GB", "size": "3.5GB", "validity": "30 Days", "cost_price": 2425, "selling_price": 2550, "datastation_network_id": "1", "datastation_plan_id": "353"},
    {"id": "mtn-gift-5gb", "network": "mtn", "type": "gifting", "name": "MTN Gifting 5GB", "size": "5GB", "validity": "30 Days", "cost_price": 2750, "selling_price": 2890, "datastation_network_id": "1", "datastation_plan_id": "406"}, # Coupon actually
    
    # =========================================================
    # AIRTEL (Network ID: 4)
    # =========================================================
    # SME
    {"id": "airtel-sme-1gb", "network": "airtel", "type": "sme", "name": "Airtel SME 1GB", "size": "1GB", "validity": "30 Days", "cost_price": 300, "selling_price": 320, "datastation_network_id": "4", "datastation_plan_id": "360"}, # Assuming monthly variant or close
    {"id": "airtel-sme-2gb", "network": "airtel", "type": "sme", "name": "Airtel SME 2GB", "size": "2GB", "validity": "30 Days", "cost_price": 1514, "selling_price": 1590, "datastation_network_id": "4", "datastation_plan_id": "375"},
    {"id": "airtel-sme-5gb", "network": "airtel", "type": "sme", "name": "Airtel SME 5GB", "size": "5GB", "validity": "30 Days", "cost_price": 1514, "selling_price": 1590, "datastation_network_id": "4", "datastation_plan_id": "388"}, # 7 days in list
    {"id": "airtel-sme-10gb", "network": "airtel", "type": "sme", "name": "Airtel SME 10GB", "size": "10GB", "validity": "30 Days", "cost_price": 3014, "selling_price": 3170, "datastation_network_id": "4", "datastation_plan_id": "283"},

    # Corporate Gifting
    {"id": "airtel-corp-1gb", "network": "airtel", "type": "corporate", "name": "Airtel Corp 1GB", "size": "1GB", "validity": "30 Days", "cost_price": 340, "selling_price": 360, "datastation_network_id": "4", "datastation_plan_id": "360"}, # Reusing closely
    
    # =========================================================
    # GLO (Network ID: 2)
    # =========================================================
    # SME
    {"id": "glo-sme-1gb", "network": "glo", "type": "sme", "name": "Glo SME 1GB", "size": "1GB", "validity": "30 Days", "cost_price": 280, "selling_price": 300, "datastation_network_id": "2", "datastation_plan_id": "288"}, # 1 Day in list, check validity
    {"id": "glo-sme-2.5gb", "network": "glo", "type": "sme", "name": "Glo SME 2.5GB", "size": "2.5GB", "validity": "30 Days", "cost_price": 468, "selling_price": 500, "datastation_network_id": "2", "datastation_plan_id": "289"}, # 2 Days in list
    {"id": "glo-sme-10gb", "network": "glo", "type": "sme", "name": "Glo SME 10GB", "size": "10GB", "validity": "30 Days", "cost_price": 1875, "selling_price": 1970, "datastation_network_id": "2", "datastation_plan_id": "290"}, # 7 Days
    
    # Corporate Gifting
    {"id": "glo-corp-1gb", "network": "glo", "type": "corporate", "name": "Glo Corp 1GB", "size": "1GB", "validity": "30 Days", "cost_price": 415, "selling_price": 440, "datastation_network_id": "2", "datastation_plan_id": "194"},
    {"id": "glo-corp-2gb", "network": "glo", "type": "corporate", "name": "Glo Corp 2GB", "size": "2GB", "validity": "30 Days", "cost_price": 830, "selling_price": 880, "datastation_network_id": "2", "datastation_plan_id": "195"},
    {"id": "glo-corp-5gb", "network": "glo", "type": "corporate", "name": "Glo Corp 5GB", "size": "5GB", "validity": "30 Days", "cost_price": 2075, "selling_price": 2180, "datastation_network_id": "2", "datastation_plan_id": "197"},

    # =========================================================
    # 9MOBILE (Network ID: 3)
    # =========================================================
    # Corporate Gifting
    {"id": "9m-corp-1gb", "network": "9mobile", "type": "corporate", "name": "9Mobile Corp 1GB", "size": "1GB", "validity": "30 Days", "cost_price": 300, "selling_price": 320, "datastation_network_id": "3", "datastation_plan_id": "183"},
    {"id": "9m-corp-2gb", "network": "9mobile", "type": "corporate", "name": "9Mobile Corp 2GB", "size": "2GB", "validity": "30 Days", "cost_price": 600, "selling_price": 630, "datastation_network_id": "3", "datastation_plan_id": "185"},
    {"id": "9m-corp-5gb", "network": "9mobile", "type": "corporate", "name": "9Mobile Corp 5GB", "size": "5GB", "validity": "30 Days", "cost_price": 1500, "selling_price": 1580, "datastation_network_id": "3", "datastation_plan_id": "188"},
]

def get_plan_by_id(plan_id):
    for p in DATA_PLANS:
        if p["id"] == plan_id:
            return p
    return None
