import os
import re
from app import app
from models import db, PriceItem
from utils.helpers import uid

def parse_bilal_doc():
    doc_path = "bilalapidoc.txt"
    if not os.path.exists(doc_path):
        print("bilalapidoc.txt not found")
        return []

    with open(doc_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    items = []
    
    # Identify indices of key sections
    data_index = -1
    cable_index = -1
    rc_index = -1
    exam_index = -1
    
    for i, line in enumerate(lines):
        if "Data Plans" in line: data_index = i
        elif "Cable Plans" in line: cable_index = i
        elif "Recharge Card Plans" in line: rc_index = i
        elif "Exam/Education Pin" in line: exam_index = i

    # --- PARSE DATA PLANS ---
    if data_index != -1:
        current_i = data_index + 1
        while current_i < len(lines):
            line_id = lines[current_i].strip()
            # If we hit another major section, stop parsing data
            if any(h in line_id for h in ["Cable Plans", "Recharge Card Plans", "PURCHASE PRODUCT"]):
                if current_i > data_index + 5: break
                
            if not line_id.isdigit():
                current_i += 1; continue
            
            if current_i + 1 >= len(lines): break
            line_data = lines[current_i+1].strip()
            parts = re.split(r'\t| {2,}', line_data)
            
            if len(parts) >= 4:
                network = parts[0].strip().lower()
                p_type = parts[1].strip().lower()
                size = parts[2].strip()
                price_str = parts[3].strip().replace('₦', '').replace(',', '')
                validity = parts[4].strip() if len(parts) > 4 else "30 days"
                try:
                    price = float(price_str)
                except:
                    price = 0.0

                items.append({
                    "service": "DATA",
                    "provider_code": line_id,
                    "name": f"{parts[0]} {parts[1]} {size}",
                    "network": network,
                    "plan_type": p_type,
                    "validity": validity,
                    "cost": price,
                    "markup_type": "PERCENT",
                    "markup_value": 5.0
                })
            current_i += 2

    # --- PARSE CABLE PLANS ---
    if cable_index != -1:
        current_i = cable_index + 1
        while current_i < len(lines):
            line_id = lines[current_i].strip()
            if any(h in line_id for h in ["Recharge Card Plans", "Exam/Education Pin", "PURCHASE PRODUCT"]):
                if current_i > cable_index + 5: break

            if not line_id.isdigit():
                current_i += 1; continue
            
            if current_i + 1 >= len(lines): break
            line_data = lines[current_i+1].strip()
            parts = re.split(r'\t| {2,}', line_data)
            
            if len(parts) >= 3:
                network = parts[0].strip().lower()
                name = parts[1].strip()
                price_str = parts[2].strip().replace('₦', '').replace(',', '')
                try:
                    price = float(price_str)
                except:
                    price = 0.0

                items.append({
                    "service": "CABLE",
                    "provider_code": line_id,
                    "name": name,
                    "network": network,
                    "plan_type": "cable",
                    "validity": "Monthly",
                    "cost": price,
                    "markup_type": "FLAT",
                    "markup_value": 0.0
                })
            current_i += 2

    # --- PARSE RECHARGE CARD PLANS ---
    rc_index = -1
    for i, line in enumerate(lines):
        if "Recharge Card Plans" in line:
            rc_index = i
            break
    
    if rc_index != -1:
        for i in range(rc_index + 1, len(lines), 2):
            line_id = lines[i].strip()
            if not line_id.isdigit(): break
            
            line_data = lines[i+1].strip()
            parts = re.split(r'\t| {2,}', line_data)
            if len(parts) >= 2:
                # Format: MTN | 100 | ... | ₦97.00
                network = parts[0].strip().lower()
                denom = parts[1].strip()
                price_str = parts[-1].strip().replace('₦', '').replace(',', '')
                
                try:
                    price = float(price_str)
                except:
                    price = 0.0

                items.append({
                    "service": "AIRTIME_PIN",
                    "provider_code": line_id,
                    "name": f"{parts[0]} N{denom} PIN",
                    "network": network,
                    "plan_type": "vtu",
                    "validity": "N/A",
                    "cost": price,
                    "markup_type": "FLAT",
                    "markup_value": 0.0
                })

    # --- PARSE EXAM PINS ---
    if exam_index != -1:
        current_i = exam_index + 1
        while current_i < len(lines):
            line_id = lines[current_i].strip()
            if "PURCHASE PRODUCT" in line_id and current_i > exam_index + 2: break

            if not line_id.isdigit():
                current_i += 1; continue
            
            if current_i + 1 >= len(lines): break
            line_data = lines[current_i+1].strip()
            parts = re.split(r'\t| {2,}', line_data)
            
            if len(parts) >= 2:
                name = parts[0].strip()
                price_str = parts[1].strip().replace('₦', '').replace(',', '')
                try:
                    price = float(price_str)
                except:
                    price = 0.0

                items.append({
                    "service": "EPIN",
                    "provider_code": line_id,
                    "name": name,
                    "network": "education",
                    "plan_type": "exam",
                    "validity": "Lifetime",
                    "cost": price,
                    "markup_type": "FLAT",
                    "markup_value": 0.0
                })
            current_i += 2

    # --- PARSE ELECTRICITY ---
    disco_index = -1
    for i, line in enumerate(lines):
        if "Disco ID" in line:
            disco_index = i
            break
    
    if disco_index != -1:
        for i in range(disco_index + 1, len(lines), 2):
            line_name = lines[i].strip()
            if not line_name or "padding" in line_name.lower(): break
            
            line_id = lines[i+1].strip()
            if not line_id.isdigit(): break

            items.append({
                "service": "ELECTRICITY",
                "provider_code": line_id,
                "name": line_name,
                "network": line_name.lower().replace(" electricity", ""),
                "plan_type": "disco",
                "validity": "N/A",
                "cost": 0, # Usually face value
                "markup_type": "FLAT",
                "markup_value": 0.0
            })

    # --- PARSE EDUCATION (EXAMS) ---
    exam_index = -1
    for i, line in enumerate(lines):
        if "Exam ID" in line:
            exam_index = i
            break
    
    if exam_index != -1:
        for i in range(exam_index + 1, len(lines), 1):
            line_data = lines[i].strip()
            if not line_data or "padding" in line_data.lower(): break
            
            # Format: WAEC \n 1 \n NECO \n 2 
            # Actually looking at doc: 431: WAEC \n 432: 1 ₦₦3,400.00
            if re.match(r'^\d+$', line_data) or "₦" in line_data: continue
            
            name = line_data
            id_price_line = lines[i+1].strip()
            id_match = re.match(r'^(\d+)\s+₦+([\d,.]+)', id_price_line)
            if id_match:
                eid = id_match.group(1)
                price_str = id_match.group(2).replace(',', '')
                items.append({
                    "service": "EPIN",
                    "provider_code": eid,
                    "name": name,
                    "network": name.lower(),
                    "plan_type": "exam",
                    "validity": "N/A",
                    "cost": float(price_str),
                    "markup_type": "FLAT",
                    "markup_value": 50.0 # 50 Naira markup for education pins
                })
            i += 1

    return items

def seed():
    plans = parse_bilal_doc()
    if not plans:
        print("No plans found to seed.")
        return

    with app.app_context():
        print(f"Parsed {len(plans)} plans. Cleaning old items...")
        PriceItem.query.filter(PriceItem.service.in_(["DATA", "CABLE", "AIRTIME_PIN", "AIRTIME"])).delete()
        
        for p in plans:
            # Generate ID that frontend can filter (starts with network and includes plan type)
            # Format: network-plantype-service-providercode-shortuuid
            item_id = f"{p['network']}-{p['plan_type'].lower()}-{p['service'].lower()}-{p['provider_code']}-{uid()[-6:]}"
            
            item = PriceItem(
                id=item_id,
                service=p["service"],
                provider_code=p["provider_code"],
                name=p["name"],
                network=p["network"],
                plan_type=p["plan_type"],
                validity=p["validity"],
                provider_cost_kobo=int(p["cost"] * 100),
                markup_type=p["markup_type"],
                markup_value=p["markup_value"],
                is_active=True
            )
            db.session.add(item)
        
        # Add Generic Airtime if not present
        existing_airtime = PriceItem.query.filter_by(service="AIRTIME").all()
        if not existing_airtime:
            for net in ["mtn", "glo", "airtel", "9mobile"]:
                item_id = f"{net}-airtime-{uid()[-6:]}"
                db.session.add(PriceItem(
                    id=item_id,
                    service="AIRTIME",
                    provider_code=net,
                    name=f"{net.upper()} Airtime",
                    network=net,
                    provider_cost_kobo=0,
                    markup_type="FLAT",
                    markup_value=0,
                    is_active=True
                ))

        db.session.commit()
        print("Database seeded with Bilal plans.")

if __name__ == "__main__":
    seed()
