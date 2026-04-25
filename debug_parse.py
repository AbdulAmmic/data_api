import os
import re

def parse_bilal_doc(doc_path="bilalapidoc.txt"):
    if not os.path.exists(doc_path):
        print(f"{doc_path} not found")
        return []
    with open(doc_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    items = []
    data_index = -1
    if "bilaldataplans.txt" in doc_path:
        data_index = 0
    for i, line in enumerate(lines):
        if "Data Plans" in line: data_index = i
    if data_index != -1:
        current_i = data_index + 1
        while current_i < len(lines):
            line_id = lines[current_i].strip()
            if not line_id.isdigit():
                print(f"[{doc_path}] Line {current_i} is not digit: {line_id}")
                current_i += 1
                continue
            if current_i + 1 >= len(lines): break
            line_data = lines[current_i+1].strip()
            parts = re.split(r'\t| {2,}', line_data)
            print(f"[{doc_path}] ID {line_id} parts: {parts}")
            if len(parts) >= 3:
                items.append(line_id)
                current_i += 2
            else:
                print(f"[{doc_path}] ID {line_id} too few parts: {len(parts)}")
                current_i += 1
    return items

print("BilalDoc:", len(parse_bilal_doc("bilalapidoc.txt")))
print("BilalDataPlans:", len(parse_bilal_doc("bilaldataplans.txt")))
