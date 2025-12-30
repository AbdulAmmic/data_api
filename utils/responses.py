def success_response(data=None, message="OK", status_code=200):
    payload = {"success": True, "message": message, "data": data or {}}
    return payload, status_code

def error_response(message="Error", status_code=400, data=None):
    payload = {"success": False, "message": message, "data": data or {}}
    return payload, status_code
