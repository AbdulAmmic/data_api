
import os
import json

def fix_encoding(filename):
    path = os.path.join(os.getcwd(), "plans", filename)
    content = None
    
    # Try reading as UTF-16 (Powershell default for >)
    try:
        with open(path, "r", encoding="utf-16") as f:
            content = f.read()
            # Test json parse
            json.loads(content)
            print(f"Read {filename} successfully as UTF-16")
    except Exception as e:
        print(f"UTF-16 read failed for {filename}: {e}")
    
    if content is None:
        # Try UTF-8 just in case
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                json.loads(content)
                print(f"Read {filename} successfully as UTF-8 (No fix needed?)")
        except Exception as e:
            print(f"UTF-8 read failed for {filename}: {e}")
            return

    # Write back as strict UTF-8
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved {filename} as UTF-8")

fix_encoding("data_plans.json")
fix_encoding("cable_plans.json")
