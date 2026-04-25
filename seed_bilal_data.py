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
    data_index = -1
    
    # If the file IS the data plans list only, we might start at 0
    if "bilaldataplans.txt" in doc_path:
        data_index = 0
    
    for i, line in enumerate(lines):
        if "Data Plans" in line: data_index = i
        elif "Cable Plans" in line and data_index == -1: pass # don't reset if we already found data in this file

    # Search for any line that starts with a number and has a network name in the next line
    for i in range(len(lines) - 1):
        line_id = lines[i].strip()
        if not line_id.isdigit():
            continue
            
        line_data = lines[i+1].strip()
        # Look for network names: MTN, GLO, AIRTEL, 9MOBILE
        if not any(net in line_data.upper() for net in ["MTN", "GLO", "AIRTEL", "9MOBILE"]):
            continue
            
        # We found a potential plan!
        # Try to parse it even with weird spacing
        # Use regex to find the price (starts with N or ₦)
        price_match = re.search(r'[₦N]([\d,.]+)', line_data)
        if not price_match:
            # Maybe price is just a number with comma?
            price_match = re.search(r'(\d{1,3}(?:,\d{3})+)', line_data)
        
        if not price_match:
            # Fallback: just split and look for something that looks like price
            parts = line_data.split()
        else:
            # Split by the price match to get what's before it
            pre_price = line_data[:price_match.start()].strip()
            post_price = line_data[price_match.end():].strip()
            parts = pre_price.split()
            price_str = price_match.group(1).replace(',', '')
            try:
                price = float(price_str)
            except:
                price = 0.0
            
            if len(parts) >= 2:
                network = parts[0].strip().lower()
                raw_type = " ".join(parts[1:-1]).lower() if len(parts) > 2 else parts[1].lower()
                size = parts[-1]
                
                if "sme" in raw_type: p_type = "sme"
                elif "corp" in raw_type or "cooperate" in raw_type: p_type = "corporate"
                else: p_type = "gifting"
                
                items.append({
                    "service": "DATA",
                    "provider_code": line_id,
                    "name": f"{parts[0]} {raw_type} {size}".strip(),
                    "network": network,
                    "plan_type": p_type,
                    "validity": post_price if post_price else "30 days",
                    "cost": price,
                    "markup_type": "PERCENT",
                    "markup_value": 5.0
                })
                continue

    # Cable and Exam pins keep original logic if they exist in file
    # (Checking bilalapidoc.txt specifically for these)
    if "bilalapidoc.txt" in doc_path:
        cable_index = -1
        exam_index = -1
        for i, line in enumerate(lines):
            if "Cable Plans" in line: cable_index = i
            elif "Exam/Education Pin" in line: exam_index = i
            
        if cable_index != -1:
            current_i = cable_index + 1
            while current_i < len(lines):
                line_id = lines[current_i].strip()
                if "PURCHASE PRODUCT" in line_id: break
                if not line_id.isdigit(): 
                    current_i += 1
                    continue
                line_data = lines[current_i+1].strip()
                parts = re.split(r'\t| {2,}', line_data)
                if len(parts) >= 3:
                    items.append({
                        "service": "CABLE",
                        "provider_code": line_id,
                        "name": parts[1].strip(),
                        "network": parts[0].strip().lower(),
                        "plan_type": "cable",
                        "validity": "Monthly",
                        "cost": float(parts[2].strip().replace('₦', '').replace(',', '') or 0),
                        "markup_type": "FLAT",
                        "markup_value": 0.0
                    })
                current_i += 2

    return items

def seed():
    with app.app_context():
        print("Starting Bilal Seed...")
        
        plans = parse_bilal_doc("bilalapidoc.txt")
        new_plans = parse_bilal_doc("bilaldataplans.txt")
        print(f"Found {len(plans)} in doc, {len(new_plans)} in plans file.")
        plans += new_plans
        
        if not plans:
            print("No plans found to seed.")
            return

        seen = set()
        unique_plans = []
        for p in plans:
            key = (p["service"], p["provider_code"])
            if key not in seen:
                seen.add(key)
                unique_plans.append(p)
        
        print(f"Total unique plans to seed: {len(unique_plans)}")

        PriceItem.query.filter(PriceItem.service.in_(["DATA", "CABLE", "AIRTIME_PIN", "AIRTIME"])).delete()
        
        airtime_networks = [("mtn", 1), ("airtel", 2), ("glo", 3), ("9mobile", 4)]
        for net_name, net_id in airtime_networks:
            unique_plans.append({
                "service": "AIRTIME",
                "provider_code": str(net_id),
                "name": f"{net_name.upper()} Airtime",
                "network": net_name,
                "plan_type": "vtu",
                "validity": "N/A",
                "cost": 0.0,
                "markup_type": "PERCENT",
                "markup_value": 0.0
            })

        for p in unique_plans:
            item_id = f"{p['network']}-{p['plan_type'].lower()}-{p['service'].lower()}-{p['provider_code']}-{uid()[-6:]}"
            item = PriceItem(
                id=item_id,
                service=p["service"],
                provider_code=p["provider_code"],
                name=p["name"],
                network=p["network"],
                plan_type=p["plan_type"],
                validity=p["validity"],
                provider_cost_kobo=int(p.get("cost", 0) * 100),
                markup_type=p["markup_type"],
                markup_value=float(p["markup_value"]),
                is_active=True
            )
            db.session.add(item)
        
        db.session.commit()
        print(f"Successfully seeded {len(unique_plans)} items.")

if __name__ == "__main__":
    seed()
