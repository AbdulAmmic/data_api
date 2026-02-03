
import re
import math

def calculate_new_price(cost):
    # 5% markup
    selling = cost * 1.05
    # Round up to nearest 10 Naira
    return math.ceil(selling / 10) * 10

def update_data_plans(file_path):
    print(f"Updating {file_path}...")
    with open(file_path, "r") as f:
        lines = f.readlines()

    new_lines = []
    count = 0
    for line in lines:
        # data_plans.py and education_plans.py use cost_price and selling_price
        # Pattern: "cost_price": 225, "selling_price": 275
        match = re.search(r'"cost_price":\s*(\d+)', line)
        if match:
            cost = int(match.group(1))
            new_selling = calculate_new_price(cost)
            
            # Replace existing selling price
            # Regex to find selling_price value
            line = re.sub(r'("selling_price":\s*)(\d+)', f'\\g<1>{new_selling}', line)
            count += 1
        new_lines.append(line)
        
    with open(file_path, "w") as f:
        f.writelines(new_lines)
    print(f"Updated {count} plans.")

def update_cable_plans(file_path):
    print(f"Updating {file_path}...")
    with open(file_path, "r") as f:
        lines = f.readlines()

    new_lines = []
    count = 0
    for line in lines:
        # cable_plans.py uses "amount": 1900
        # We assume 'amount' is essentially the cost/base price + fee (but currently fee is ignored logic-wise)
        # Actually logic says p['amount'] is what user pays.
        # We want to Markup the underlying provider price.
        # But we don't HAVE the provider price here explicitly, we just have 'amount'.
        # Assuming current 'amount' IS the provider price (since fee was ignored/separate)?
        # User said "just add 5%".
        # So we take current amount, treat it as cost, add 5%, save as new amount.
        
        match = re.search(r'"amount":\s*(\d+)', line)
        if match:
            current_amt = int(match.group(1))
            # Heuristic: If it looks like a price (not an ID like "1"), update it.
            # Plan IDs are strings, amounts are ints.
            
            # Problem: If current_amount already included profit? 
            # User wants 5% markup.
            # Let's assume current list is standard provider price.
            new_amt = calculate_new_price(current_amt)
            
            line = re.sub(r'("amount":\s*)(\d+)', f'\\g<1>{new_amt}', line)
            count += 1
        new_lines.append(line)
        
    with open(file_path, "w") as f:
        f.writelines(new_lines)
    print(f"Updated {count} cable plans.")

if __name__ == "__main__":
    base_dir = r"c:\Users\IMLUX\Documents\works\dataapp\VTUMAJIRE_API\plans"
    
    update_data_plans(f"{base_dir}\\data_plans.py")
    update_data_plans(f"{base_dir}\\education_plans.py")
    update_cable_plans(f"{base_dir}\\cable_plans.py")
