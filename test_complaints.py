import requests
import json
import sys

BASE_URL = "http://127.0.0.1:5000/api"

def login(email, password):
    url = f"{BASE_URL}/auth/login"
    payload = {"email": email, "password": password}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()['data']['token']
    except Exception as e:
        print(f"Login failed: {e}")
        if response:
            print(response.text)
        sys.exit(1)

def test_complaints_flow():
    print("--- Testing Complaints System ---")
    
    # 1. Login as User
    print("\n[User] Logging in...")
    # Assuming 'user@example.com' exists from previous seeds or registration
    # If not, this might fail. We'll try to register if login fails or just use a known user.
    # For now, let's assume the user created in seed_admin (if any) or a test user.
    # Actually, seed_admin created 'admin'. Let's use admin for both for simplicity, 
    # or better, create a temporary user if possible.
    # Let's try to register a new user for this test to be clean.
    
    import uuid
    random_suffix = str(uuid.uuid4())[:8]
    email = f"test_user_{random_suffix}@example.com"
    password = "password123"
    
    # Register User
    print(f"[User] Registering {email}...")
    reg_payload = {
        "email": email, "password": password, 
        "first_name": "Test", "last_name": "User", "phone": f"080{random_suffix[:8]}" # Ensure phone is somewhat unique/valid length
    }
    # Pad phone to 11 digits
    reg_payload["phone"] = "080" + str(uuid.uuid4().int)[:8] 
    
    res = requests.post(f"{BASE_URL}/auth/register", json=reg_payload)
    if res.status_code != 201:
        print(f"Registration failed: {res.text}")
        # If reg fails, we can't login.
        sys.exit(1)
        
    user_token = login(email, password)
    print("[User] Logged in.")

    # 2. Create Complaint
    print("\n[User] Creating complaint...")
    complaint_data = {
        "subject": "Test Complaint API",
        "message": "This is a test complaint from the verification script."
    }
    res = requests.post(f"{BASE_URL}/support/complaints", json=complaint_data, headers={"Authorization": f"Bearer {user_token}"})
    if res.status_code == 201:
        print("✅ Complaint created successfully.")
        complaint_id = res.json()['data']['id']
    else:
        print(f"❌ Failed to create complaint: {res.text}")
        return

    # 3. List Complaints (User)
    print("\n[User] Listing complaints...")
    res = requests.get(f"{BASE_URL}/support/complaints", headers={"Authorization": f"Bearer {user_token}"})
    if res.status_code == 200:
        complaints = res.json()['data']['complaints']
        print(f"✅ User sees {len(complaints)} complaints.")
    else:
        print(f"❌ Failed to list complaints: {res.text}")

    # 4. Login as Admin
    print("\n[Admin] Logging in...")
    # Assuming default admin credentials or the one from seed_admin
    admin_token = login("admin@example.com", "admin123") # Update if your seed uses different creds
    print("[Admin] Logged in.")

    # 5. List Complaints (Admin)
    print("\n[Admin] Listing all complaints...")
    res = requests.get(f"{BASE_URL}/admin/complaints", headers={"Authorization": f"Bearer {admin_token}"})
    if res.status_code == 200:
        all_complaints = res.json()['data']['complaints']
        print(f"✅ Admin sees {len(all_complaints)} complaints.")
        
        # Verify our specific complaint is there
        found = any(c['id'] == complaint_id for c in all_complaints)
        if found:
            print("✅ Created complaint found in admin list.")
        else:
            print("❌ Created complaint NOT found in admin list.")
    else:
        print(f"❌ Failed to list complaints as admin: {res.text}")

    # 6. Resolve Complaint
    print("\n[Admin] Resolving complaint...")
    resolve_data = {
        "reply": "This has been resolved by the admin script.",
        "status": "RESOLVED"
    }
    res = requests.patch(f"{BASE_URL}/admin/complaints/{complaint_id}/resolve", json=resolve_data, headers={"Authorization": f"Bearer {admin_token}"})
    if res.status_code == 200:
        print("✅ Complaint resolved successfully.")
    else:
        print(f"❌ Failed to resolve complaint: {res.text}")

    # 7. Verify Resolution (User)
    print("\n[User] Checking resolution...")
    res = requests.get(f"{BASE_URL}/support/complaints", headers={"Authorization": f"Bearer {user_token}"})
    if res.status_code == 200:
        complaints = res.json()['data']['complaints']
        target = next((c for c in complaints if c['id'] == complaint_id), None)
        if target:
            print(f"Complaint Status: {target['status']}")
            print(f"Admin Reply: {target['admin_reply']}")
            if target['status'] == 'RESOLVED' and target['admin_reply']:
                print("✅ User sees correct status and reply.")
            else:
                print("❌ User does NOT see updated status/reply.")
        else:
            print("❌ Complaint missing from user list.")
            
if __name__ == "__main__":
    try:
        test_complaints_flow()
    except Exception as e:
        print(f"Test failed with exception: {e}")
