# test_render_google_auth.py
import requests
import json
import webbrowser
import urllib.parse

BASE_URL = "https://bibel-quiz.onrender.com"

def test_health_check():
    """Test if the API is running"""
    print("\n" + "="*60)
    print("1. TESTING HEALTH CHECK")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/health/", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ API is running: {response.json()}")
            return True
        else:
            print(f"❌ API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot reach API: {e}")
        return False

def test_google_redirect():
    """Test getting Google auth URL"""
    print("\n" + "="*60)
    print("2. TESTING GOOGLE AUTH REDIRECT")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/auth/google/redirect/", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if data.get('status') == 'success' and data.get('data', {}).get('auth_url'):
                auth_url = data['data']['auth_url']
                print(f"\n✅ Google auth URL generated successfully!")
                print(f"\n📱 Auth URL:\n{auth_url}")
                
                # Ask user if they want to open the URL
                choice = input("\n🌐 Open this URL in browser? (yes/no): ")
                if choice.lower() == 'yes':
                    webbrowser.open(auth_url)
                return auth_url
            else:
                print(f"❌ Invalid response structure")
                return None
        else:
            print(f"❌ Failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_google_callback(code):
    """Test exchanging code for tokens"""
    print("\n" + "="*60)
    print("3. TESTING GOOGLE CALLBACK")
    print("="*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/google/callback/",
            json={"code": code},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if data.get('status') == 'success':
                tokens = data.get('data', {})
                print(f"\n✅ Login successful!")
                print(f"👤 User: {tokens.get('user', {}).get('email')}")
                print(f"🆕 New user: {tokens.get('is_new_user', False)}")
                print(f"🔑 Access Token: {tokens.get('access_token', '')[:50]}...")
                
                # Save token to file
                with open('access_token.txt', 'w') as f:
                    f.write(tokens.get('access_token', ''))
                print(f"\n💾 Access token saved to: access_token.txt")
                
                return tokens.get('access_token')
            else:
                print(f"❌ Login failed: {data.get('message')}")
                return None
        else:
            print(f"❌ Failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_protected_endpoint(token):
    """Test a protected endpoint with the token"""
    print("\n" + "="*60)
    print("4. TESTING PROTECTED ENDPOINT")
    print("="*60)
    
    if not token:
        print("⚠️ No token available, skipping...")
        return
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/user/profile/",
            headers=headers,
            timeout=10
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Protected endpoint accessible!")
            print(f"👤 User profile: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Protected endpoint failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_with_direct_token(access_token):
    """Test login with direct access token"""
    print("\n" + "="*60)
    print("5. TESTING DIRECT TOKEN LOGIN")
    print("="*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/google/",
            json={"access_token": access_token},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Direct token login successful!")
            print(f"Response: {json.dumps(data, indent=2)}")
            return data.get('data', {}).get('access_token')
        else:
            print(f"❌ Direct token login failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def interactive_test():
    """Interactive test for Google OAuth"""
    print("\n" + "="*60)
    print("🔐 GOOGLE OAUTH TEST SUITE")
    print("="*60)
    print(f"🌐 API Base URL: {BASE_URL}")
    
    # Test 1: Health check
    if not test_health_check():
        print("\n❌ API is not accessible. Make sure your Render service is running.")
        return
    
    # Test 2: Get redirect URL
    auth_url = test_google_redirect()
    
    if not auth_url:
        print("\n❌ Failed to get Google auth URL. Check your configuration.")
        return
    
    print("\n" + "="*60)
    print("📋 MANUAL STEPS REQUIRED")
    print("="*60)
    print("1. Open the Google auth URL in your browser")
    print("2. Sign in with your Google account")
    print("3. Authorize the application")
    print("4. After redirect, copy the 'code' parameter from the URL")
    print("\nExample URL after redirect:")
    print(f"{BASE_URL}/api/auth/google/callback/?code=4/0AY0e-g7...")
    
    # Ask for the code
    code = input("\n📝 Paste the authorization code from the URL: ").strip()
    
    if code:
        # Test 3: Exchange code for tokens
        token = test_google_callback(code)
        
        if token:
            # Test 4: Access protected endpoint
            test_protected_endpoint(token)
        else:
            print("\n❌ Failed to get access token. Check your code.")
    else:
        print("\n⚠️ No code provided. Skipping token exchange.")

def automated_test_with_token():
    """Automated test if you already have a token"""
    print("\n" + "="*60)
    print("🔐 AUTOMATED TOKEN TEST")
    print("="*60)
    
    # Try to load existing token
    try:
        with open('access_token.txt', 'r') as f:
            token = f.read().strip()
            print(f"✅ Loaded existing token from file")
            test_protected_endpoint(token)
    except:
        print("⚠️ No existing token found. Run interactive test first.")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔧 GOOGLE OAUTH TEST TOOL")
    print("="*60)
    print("\nSelect test mode:")
    print("1. Interactive test (full OAuth flow)")
    print("2. Test with existing token")
    print("3. Quick health check only")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    if choice == '1':
        interactive_test()
    elif choice == '2':
        automated_test_with_token()
    elif choice == '3':
        test_health_check()
    else:
        print("Invalid choice")
    
    print("\n" + "="*60)
    print("✅ Test complete!")
    print("="*60)