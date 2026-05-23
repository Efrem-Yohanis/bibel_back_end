# test_simple.py
import requests

BASE_URL = "http://127.0.0.1:8009"

# Login first
login_response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={
        "username_or_email": "testuser_20260522_215225",
        "password": "Test123456!"
    }
)

print(f"Login status: {login_response.status_code}")
login_data = login_response.json()
print(f"Login response: {login_data}")

if login_response.status_code == 200:
    token = login_data['data']['access_token']
    print(f"Token: {token}")
    
    # Now make the profile request
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    profile_response = requests.get(
        f"{BASE_URL}/api/user/profile",
        headers=headers
    )
    
    print(f"\nProfile status: {profile_response.status_code}")
    print(f"Profile response: {profile_response.json()}")