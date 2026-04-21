import json
import os

PLANS_FILE = os.path.join(os.path.dirname(__file__), "plans", "data_plans.json")

with open(PLANS_FILE, "r", encoding="utf-8") as f:
    plans = json.load(f)

updated = 0
for plan in plans:
    cost = plan["cost_price"]
    old_selling = plan["selling_price"]
    new_selling = round(cost + 15, 2)
    plan["selling_price"] = new_selling
    print(f"  [{plan['network']}] {plan['name']}")
    print(f"    cost=₦{cost}  old_selling=₦{old_selling}  new_selling=₦{new_selling}  profit=+₦15")
    updated += 1

with open(PLANS_FILE, "w", encoding="utf-8") as f:
    json.dump(plans, f, indent=4, ensure_ascii=False)

print(f"\n✅ Done. Updated {updated} plans. All plans now have ₦15 profit over cost price.")
