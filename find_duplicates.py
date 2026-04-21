import json
import os
from collections import defaultdict

PLANS_FILE = os.path.join(os.path.dirname(__file__), "plans", "data_plans.json")
REPORT_FILE = os.path.join(os.path.dirname(__file__), "duplicates_report.txt")

with open(PLANS_FILE, "r", encoding="utf-8") as f:
    plans = json.load(f)

# Group by (network, size, validity)
groups = defaultdict(list)
for plan in plans:
    key = (plan["network"], plan["size"].strip(), plan["validity"].strip())
    groups[key].append(plan)

lines = ["=== DUPLICATE PLANS (same network + size + validity) ===\n"]
dup_count = 0
for key, group in groups.items():
    if len(group) > 1:
        dup_count += 1
        network, size, validity = key
        lines.append(f"[{network.upper()}] {size} / {validity}  ({len(group)} entries):")
        for p in group:
            lines.append(f"   id={p['id']}  type={p['type']}  cost=N{p['cost_price']}  selling=N{p['selling_price']}")
        lines.append("")

if dup_count == 0:
    lines.append("No duplicates found.")
else:
    lines.append(f"Total duplicate groups: {dup_count}")

report = "\n".join(lines)
print(report)
with open(REPORT_FILE, "w", encoding="utf-8") as f:
    f.write(report)
