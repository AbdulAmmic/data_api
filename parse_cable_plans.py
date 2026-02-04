
import json

raw_data = """
2	GOtv Max	8500
6	DStv Yanga	6000
7	DStv Compact	19000
8	DStv Compact Plus	30000
9	DStv Premium	44500
11	Classic -6000 Naira - 1 Month	6000
13	Smart - 5100 Naira - 1 Month	5100
14	Nova - 2100 Naira - 1 Month	2100
15	Super - 9800 Naira - 1 Month	9800
16	GOtv Jinja	3900
17	GOtv Jolli	5800
19	DStv Confam	11000
20	DStv Padi	4400
21	DStv Great Wall Standalone	3800
24	DStv Premium French	69000
25	DStv Premium Asia	50500
26	DStv Confam + ExtraView	17000
27	DStv Yanga + ExtraView	12000
28	DStv Padi + ExtraView	10400
29	DStv Compact + Extra View	25000
30	DStv Premium + Extra View	50500
31	DStv Compact Plus - Extra View	36000
33	ExtraView Access	6000
34	GOtv Smallie - Monthly	1900
35	GOtv Smallie - Quarterly	5100
36	GOtv Smallie - Yearly	15000
37	Nova - 700 Naira - 1 Week	700
38	Basic - 1100 Naira - 1 Week	1400
39	Smart - 1700 Naira - 1 Week	1700
40	Classic - 2000 Naira - 1 Week	2000
41	Super - 3300 Naira - 1 Week	3300
47	Supa plus - 16800 Naira - 1 Month	16800
48	GOtv Supa - monthly	11400
49	Basic - 3300 - 1 Month	3300
"""

lines = raw_data.strip().split('\n')
output = "CABLE_PLANS = [\n"

for line in lines:
    parts = line.split('\t')
    if len(parts) < 3:
        continue
        
    pid = parts[0].strip()
    name = parts[1].strip()
    amount_str = parts[2].strip().replace('₦', '').replace(',', '')
    
    try:
        amount = float(amount_str)
    except:
        amount = 0.0

    cable_id = "3" # Default to StarTimes
    if "GOtv" in name or "GOtv" in name:
        cable_id = "1"
    elif "DStv" in name or "DStv" in name:
        cable_id = "2"
    
    # Special handle for "ExtraView Access" and "Supa plus" which belongs to GOtv? OR Dstv?
    # Supa plus matches GOtv Supa.
    if "Supa" in name: cable_id = "1"
    # ExtraView is DStv feature.
    if "ExtraView" in name: cable_id = "2"

    # ID slug
    slug = name.lower().replace(" ", "-").replace("+", "plus").replace("/", "-")
    # Clean up weird chars
    slug = "".join([c for c in slug if c.isalnum() or c == '-'])
    internal_id = f"{slug}-{pid}"
    
    # Selling price: Amount + 100 fee? 
    # Old file had `amount` (selling price) and `fee`.
    # Controller says: `amount_naira = plan_conf["amount"]` (Selling Price).
    # Services are usually sold with a fee (convenience fee)
    # The list provided by user likely shows the PROVIDER AMOUNT (Cost).
    # If I sell at that price, I make 0 or lose money if there is a fee.
    # Usually we add 50-100 naira.
    # I'll set 'amount' (Selling Price) = cost + 100.
    
    selling_price = amount + 50
    if amount == 0: selling_price = 0

    output += "    {\n"
    output += f'        "id": "{internal_id}",\n'
    output += f'        "cable_id": "{cable_id}",\n'
    output += f'        "package_id": "{pid}",\n'
    output += f'        "name": "{name}",\n'
    output += f'        "amount": {selling_price},\n' 
    output += "    },\n"

output += "]\n\n"
output += """def get_cable_plan(plan_id):
    for p in CABLE_PLANS:
        if p["id"] == plan_id:
            return p
    return None
"""

with open("plans/cable_plans.py", "w", encoding='utf-8') as f:
    f.write(output)

print("Done")
