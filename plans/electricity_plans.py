
# Electricity Discos
# Derived from user provided list

ELECTRICITY_DISCOS = [
    {"id": "ikeja-electric", "disco_id": "1", "name": "Ikeja Electric"},
    {"id": "eko-electric", "disco_id": "2", "name": "Eko Electric"},
    {"id": "abuja-electric", "disco_id": "3", "name": "Abuja Electric"},
    {"id": "kano-electric", "disco_id": "4", "name": "Kano Electric"},
    {"id": "enugu-electric", "disco_id": "5", "name": "Enugu Electric"},
    {"id": "ph-electric", "disco_id": "6", "name": "Port Harcourt Electric"},
    {"id": "ibadan-electric", "disco_id": "7", "name": "Ibadan Electric"},
    {"id": "kaduna-electric", "disco_id": "8", "name": "Kaduna Electric"},
    {"id": "jos-electric", "disco_id": "9", "name": "Jos Electric"},
    {"id": "benin-electric", "disco_id": "10", "name": "Benin Electric"},
    {"id": "yola-electric", "disco_id": "11", "name": "Yola Electric"},
]

def get_disco(disco_id):
    for d in ELECTRICITY_DISCOS:
        if d["id"] == disco_id:
            return d
    return None
