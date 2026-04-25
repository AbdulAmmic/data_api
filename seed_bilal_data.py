import os
import re
from app import app
from models import db, PriceItem
from utils.helpers import uid

def parse_bilal_doc(doc_path="bilalapidoc.txt"):
    if not os.path.exists(doc_path):
        print(f"{doc_path} not found")
        return []

    with open(doc_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    items = []
    
    # Generic loop for all digit-prefixed plans
    for i in range(len(lines) - 1):
        line_id = lines[i].strip()
        if not line_id.isdigit():
            continue
            
        line_data = lines[i+1].strip()
        
        # 1. DATA PLANS
        if any(net in line_data.upper() for net in ["MTN", "GLO", "AIRTEL", "9MOBILE"]):
            price_match = re.search(r'[₦N]([\d,.]+)', line_data)
            if price_match:
                pre_price = line_data[:price_match.start()].strip()
                post_price = line_data[price_match.end():].strip()
                parts = pre_price.split()
                price_str = price_match.group(1).replace(',', '')
                try: price = float(price_str)
                except: price = 0.0
                
                if len(parts) >= 2:
                    network = parts[0].strip().lower()
                    raw_type = " ".join(parts[1:-1]).lower() if len(parts) > 2 else parts[1].lower()
                    size = parts[-1]
                    if "sme" in raw_type: p_type = "sme"
                    elif "corp" in raw_type or "cooperate" in raw_type: p_type = "corporate"
                    else: p_type = "gifting"
                    
                    items.append({
                        "service": "DATA", "provider_code": line_id, "name": f"{parts[0]} {raw_type} {size}".strip(),
                        "network": network, "plan_type": p_type, "validity": post_price if post_price else "30 days",
                        "cost": price, "markup_type": "PERCENT", "markup_value": 5.0
                    })
                    continue

        # 2. CABLE PLANS
        if any(cab in line_data.upper() for cab in ["DSTV", "GOTV", "STARTIME", "SHOWMAX"]):
            price_match = re.search(r'[₦N]([\d,.]+)', line_data)
            if price_match:
                pre_price = line_data[:price_match.start()].strip()
                parts = pre_price.split()
                price_str = price_match.group(1).replace(',', '')
                try: price = float(price_str)
                except: price = 0.0
                
                if len(parts) >= 2:
                    network = parts[0].strip().lower()
                    name = " ".join(parts[1:])
                    items.append({
                        "service": "CABLE", "provider_code": line_id, "name": name,
                        "network": network, "plan_type": "cable", "validity": "Monthly",
                        "cost": price, "markup_type": "FLAT", "markup_value": 0.0
                    })
                    continue

    # Special sections
    elec_index = -1
    epin_index = -1
    pin_index = -1
    for i, line in enumerate(lines):
        if "Disco ID" in line: elec_index = i
        elif "Exam ID" in line: epin_index = i
        elif "Recharge Card Plans" in line: pin_index = i

    if elec_index != -1:
        for i in range(elec_index + 1, len(lines), 2):
            if i+1 >= len(lines): break
            name = lines[i].strip()
            code = lines[i+1].strip()
            if not code.isdigit(): break
            items.append({
                "service": "ELECTRICITY", "provider_code": code, "name": name,
                "network": name.split()[0].lower(), "plan_type": "prepaid", "validity": "N/A",
                "cost": 0.0, "markup_type": "FLAT", "markup_value": 0.0
            })

    if epin_index != -1:
        for i in range(epin_index + 1, len(lines), 2):
            if i+1 >= len(lines): break
            name = lines[i].strip()
            details = lines[i+1].strip()
            parts = details.split()
            if not parts[0].isdigit(): break
            price_str = parts[1].replace('₦', '').replace(',', '') if len(parts) > 1 else "0"
            items.append({
                "service": "EPIN", "provider_code": parts[0], "name": f"{name} PIN",
                "network": "education", "plan_type": "exam", "validity": "Lifetime",
                "cost": float(price_str or 0), "markup_type": "FLAT", "markup_value": 0.0
            })

    if pin_index != -1:
        for i in range(pin_index + 1, len(lines), 2):
            if i+1 >= len(lines): break
            code = lines[i].strip()
            if not code.isdigit(): break
            details = lines[i+1].strip()
            parts = details.split()
            price_str = parts[-1].replace('₦', '').replace(',', '')
            items.append({
                "service": "AIRTIME_PIN", "provider_code": code, "name": f"{parts[0]} {parts[1]} PIN",
                "network": parts[0].lower(), "plan_type": "recharge", "validity": "N/A",
                "cost": float(price_str or 0), "markup_type": "FLAT", "markup_value": 0.0
            })

    return items

def seed():
    with app.app_context():
        print("Starting Bilal Seed...")
        plans = parse_bilal_doc("bilalapidoc.txt")
        plans += parse_bilal_doc("bilaldataplans.txt")
        
        seen = set()
        unique_plans = []
        for p in plans:
            key = (p["service"], p["provider_code"])
            if key not in seen:
                seen.add(key)
                unique_plans.append(p)
        
        print(f"Total unique plans from docs: {len(unique_plans)}")
        
        PriceItem.query.delete() # Reset
        
        # Standard Airtime
        for net_name, net_id in [("mtn", 1), ("airtel", 2), ("glo", 3), ("9mobile", 4)]:
            item = PriceItem(
                id=f"{net_name}-airtime-{uid()[-6:]}", service="AIRTIME", provider_code=str(net_id),
                name=f"{net_name.upper()} Airtime", network=net_name, plan_type="vtu",
                validity="N/A", provider_cost_kobo=0, markup_type="PERCENT", markup_value=0.0, is_active=True
            )
            db.session.add(item)

        for p in unique_plans:
            item_id = f"{p['network']}-{p['plan_type'].lower()}-{p['service'].lower()}-{p['provider_code']}-{uid()[-6:]}"
            item = PriceItem(
                id=item_id, service=p["service"], provider_code=p["provider_code"],
                name=p["name"], network=p["network"], plan_type=p["plan_type"],
                validity=p["validity"], provider_cost_kobo=int(p.get("cost", 0) * 100),
                markup_type=p["markup_type"], markup_value=float(p["markup_value"]), is_active=True
            )
            db.session.add(item)
        
        db.session.commit()
        print("Successfully seeded all items.")

if __name__ == "__main__":
    seed()
