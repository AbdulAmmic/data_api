import json
import os

def update_plans():
    path = os.path.join("plans", "data_plans.json")
    with open(path, "r", encoding="utf-8") as f:
        plans = json.load(f)

    # Peyflex Networks Mapping
    network_map = {
        "mtn": {"gifting": "mtn_gifting_data", "sme": "mtn_sme_data", "sme2": "mtn_sme2_data", "corporate": "mtn_cg_data"},
        "airtel": {"gifting": "airtel_gifting_data", "sme": "airtel_sme_data", "corporate": "airtel_cg_data"},
        "glo": {"gifting": "glo_gifting_data", "corporate": "glo_cg_data", "sme": "glo_sme_data"},
        "9mobile": {"gifting": "9mobile_gifting_data", "corporate": "9mobile_cg_data", "sme": "9mobile_sme_data"}
    }

    # Updating the JSON file keys to match peyflex structures
    for plan in plans:
        net = plan["network"].lower()
        typ = plan["type"].lower()
        
        # Determine peyflex network string
        pf_net = network_map.get(net, {}).get(typ, f"{net}_{typ}_data")
        plan["datastation_network_id"] = pf_net
        
        # Set a placeholder for plan_id since we can't fetch them automatically yet
        # Peyflex plan IDs often look like "M110MBS" for MTN Gifting etc. 
        # The frontend fetches them fresh so they exist, but backend needs them.
        # Let's map a few known ones for testing if possible or instruct the user to sync them.
        
    with open(path, "w", encoding="utf-8") as f:
        json.dump(plans, f, indent=4)

if __name__ == "__main__":
    update_plans()
    print("Done")
