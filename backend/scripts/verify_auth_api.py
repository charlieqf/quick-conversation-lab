
import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_login(username, password):
    print(f"Testing login for {username}...")
    try:
        response = requests.post(f"{BASE_URL}/api/auth/token", data={
            "username": username,
            "password": password
        })
        if response.status_code == 200:
            print("  Login Successful")
            return response.json()
        else:
            print(f"  Login Failed: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print(f"  Connection Error: {e}")
        return None

def test_profile(token, expected_role):
    print(f"Testing profile access (Expect role={expected_role})...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/users/profile", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        role = data.get("role")
        print(f"  Profile Access Successful. Role: {role}")
        if role == expected_role:
             print("  [PASS] Role matches.")
        else:
             print(f"  [FAIL] Role mismatch. Got {role}, expected {expected_role}")
    else:
        print(f"  [FAIL] Profile Access Failed: {response.status_code}")

def main():
    print("=== API VERIFICATION START ===")
    
    # 1. Admin Login
    admin_token_data = test_login("admin", "admin")
    if admin_token_data:
        test_profile(admin_token_data["access_token"], "admin")
    
    print("-" * 20)

    # 2. User Login
    user_token_data = test_login("user1", "user1")
    if user_token_data:
        test_profile(user_token_data["access_token"], "user")

    print("-" * 20)
    
    # 3. Invalid Login
    print("Testing invalid login...")
    bad_token = test_login("admin", "wrongpassword")
    if bad_token is None:
        print("  [PASS] Invalid login correctly rejected.")
    else:
        print("  [FAIL] Invalid login was accepted!")

    print("=== API VERIFICATION END ===")

if __name__ == "__main__":
    main()
