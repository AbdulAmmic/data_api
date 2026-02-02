
# Education PINs
# Pricing includes markup

EDUCATION_PLANS = [
    {
        "id": "waec", 
        "exam_name": "WAEC", 
        "label": "WAEC Result Checker", 
        "cost_price": 3500, 
        "selling_price": 3800,
        "datastation_id": "WAEC" # Verify if this is the exact string required? Params say 'exam_name'
    },
    {
        "id": "neco", 
        "exam_name": "NECO", 
        "label": "NECO Result Checker", 
        "cost_price": 1200, 
        "selling_price": 1500,
        "datastation_id": "NECO"
    },
    {
        "id": "nabteb", 
        "exam_name": "NABTEB", 
        "label": "NABTEB Result Checker", 
        "cost_price": 1000, 
        "selling_price": 1300, 
        "datastation_id": "NABTEB"
    },
]

def get_education_plan(plan_id):
    for p in EDUCATION_PLANS:
        if p["id"] == plan_id:
            return p
    return None
