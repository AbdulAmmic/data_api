
# Cable TV Packages
# Derived from user provided list

CABLE_PLANS = [
    # --- GOTV (Cable ID: 1) ---
    {"id": "gotv-smallie-monthly", "cable_id": "1", "package_id": "34", "name": "GOtv Smallie - Monthly", "amount": 2000, "fee": 100},
    {"id": "gotv-jinja", "cable_id": "1", "package_id": "16", "name": "GOtv Jinja", "amount": 4100, "fee": 100},
    {"id": "gotv-jolli", "cable_id": "1", "package_id": "17", "name": "GOtv Jolli", "amount": 6090, "fee": 100},
    {"id": "gotv-max", "cable_id": "1", "package_id": "2", "name": "GOtv Max", "amount": 8930, "fee": 100},
    {"id": "gotv-supa", "cable_id": "1", "package_id": "47", "name": "GOtv Supa", "amount": 11970, "fee": 100},
    {"id": "gotv-supa-plus", "cable_id": "1", "package_id": "48", "name": "GOtv Supa Plus", "amount": 17640, "fee": 100},

    # --- DSTV (Cable ID: 2) ---
    {"id": "dstv-padi", "cable_id": "2", "package_id": "20", "name": "DStv Padi", "amount": 4620, "fee": 100},
    {"id": "dstv-yanga", "cable_id": "2", "package_id": "6", "name": "DStv Yanga", "amount": 6300, "fee": 100},
    {"id": "dstv-confam", "cable_id": "2", "package_id": "19", "name": "DStv Confam", "amount": 11550, "fee": 100},
    {"id": "dstv-compact", "cable_id": "2", "package_id": "7", "name": "DStv Compact", "amount": 19950, "fee": 100},
    {"id": "dstv-compact-plus", "cable_id": "2", "package_id": "8", "name": "DStv Compact Plus", "amount": 31500, "fee": 100},
    {"id": "dstv-premium", "cable_id": "2", "package_id": "9", "name": "DStv Premium", "amount": 46730, "fee": 100},
    
    # --- STARTIMES (Cable ID: 3) ---
    {"id": "startimes-nova-week", "cable_id": "3", "package_id": "37", "name": "Nova - Weekly", "amount": 740, "fee": 50},
    {"id": "startimes-nova-month", "cable_id": "3", "package_id": "14", "name": "Nova - Monthly", "amount": 2210, "fee": 50},
    {"id": "startimes-basic-week", "cable_id": "3", "package_id": "38", "name": "Basic - Weekly", "amount": 1470, "fee": 50},
    {"id": "startimes-basic-month", "cable_id": "3", "package_id": "49", "name": "Basic - Monthly", "amount": 4200, "fee": 50},
    {"id": "startimes-smart-week", "cable_id": "3", "package_id": "39", "name": "Smart - Weekly", "amount": 1790, "fee": 50},
    {"id": "startimes-smart-month", "cable_id": "3", "package_id": "13", "name": "Smart - Monthly", "amount": 5360, "fee": 50},
    {"id": "startimes-classic-week", "cable_id": "3", "package_id": "40", "name": "Classic - Weekly", "amount": 2100, "fee": 50},
    {"id": "startimes-classic-month", "cable_id": "3", "package_id": "11", "name": "Classic - Monthly", "amount": 6300, "fee": 50},
    {"id": "startimes-super-week", "cable_id": "3", "package_id": "41", "name": "Super - Weekly", "amount": 3470, "fee": 50},
    {"id": "startimes-super-month", "cable_id": "3", "package_id": "15", "name": "Super - Monthly", "amount": 10290, "fee": 50},
]

def get_cable_plan(plan_id):
    for p in CABLE_PLANS:
        if p["id"] == plan_id:
            return p
    return None
