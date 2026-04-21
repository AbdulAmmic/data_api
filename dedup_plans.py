import json
import os
from collections import defaultdict

PLANS_FILE = os.path.join(os.path.dirname(__file__), "plans", "data_plans.json")

with open(PLANS_FILE, "r", encoding="utf-8") as f:
    plans = json.load(f)

# IDs to REMOVE (keep the better/cheaper one from each duplicate group)
ids_to_remove = {
    # [AIRTEL] 1.0 GB / 3 days (Social) - same cost, keep sme, remove corporate
    "airtel-corporate-1.0gb-367",

    # [AIRTEL] 10.0 GB / 30 days - sme is cheaper (N3050), remove corporate (N4045)
    "airtel-corporate-10.0gb-381",

    # [AIRTEL] 1.5 GB / 2 days - same cost, keep sme, remove corporate
    "airtel-corporate-1.5gb-387",

    # [AIRTEL] 2.0 GB / 2 days - same cost, keep sme, remove corporate
    "airtel-corporate-2.0gb-386",

    # [AIRTEL] 5.0 GB / 7 days - same cost, keep sme, remove corporate
    "airtel-corporate-5.0gb-385",

    # [MTN] 6.0 GB / 7 days - sme is cheaper (N2450), remove gifting (N2460)
    "mtn-gifting-6.0gb-219",

    # [MTN] 11.0 GB / 7 days - gifting is cheaper (N3430), remove sme (N3465)
    "mtn-sme-11.0gb-408",

    # [MTN] 3.0 GB / 30 days - sme2 is cheaper (N1680), remove sme (N1980)
    "mtn-sme-3.0gb-336",

    # [MTN] 1.0 GB / 7 days (3 entries) - sme2 cheapest (N560), remove sme + gifting
    "mtn-sme-1.0gb-340",
    "mtn-gifting-1.0gb-415",

    # [MTN] 5.0 GB / 30 days - sme2 cheaper (N2800), remove sme (N3100)
    "mtn-sme-5.0gb-372",

    # [MTN] 1.0 GB / 1 day - same cost, keep sme, remove gifting
    "mtn-gifting-1.0gb-423",

    # [MTN] 2.5 GB / 1 day - same cost, keep sme, remove gifting
    "mtn-gifting-2.5gb-424",
}

before = len(plans)
cleaned = [p for p in plans if p["id"] not in ids_to_remove]
after = len(cleaned)

with open(PLANS_FILE, "w", encoding="utf-8") as f:
    json.dump(cleaned, f, indent=4, ensure_ascii=False)

print(f"Removed {before - after} duplicate plans. ({before} -> {after} total)")
for rid in sorted(ids_to_remove):
    print(f"  - removed: {rid}")
