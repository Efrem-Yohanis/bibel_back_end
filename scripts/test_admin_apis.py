"""
Admin API Test Script
Tests admin user management endpoints
"""

import argparse
import requests
import sys
from typing import Optional, Dict, Any


class AdminAPITester:
    def __init__(self, base_url: str, admin_username: str, admin_password: str, timeout: int = 15):
        self.base_url = base_url.rstrip('/')
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.timeout = timeout
        self.access_token: Optional[str] = None
        self.admin_user_id: Optional[int] = None

    def login(self) -> bool:
        """Login as admin and get access token"""
        url = f"{self.base_url}/api/auth/login"
        payload = {
            "username_or_email": self.admin_username,
            "password": self.admin_password
        }
        
        print(f"\n[LOGIN] POST {url}")
        print(f"Payload: {payload}")
        
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            print(f"Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error: {response.text}")
                return False
            
            data = response.json()
            self.access_token = data['data']['access_token']
            self.admin_user_id = data['data']['user_id']
            print(f"✓ Login successful. Token: {self.access_token[:20]}...")
            print(f"✓ Admin user ID: {self.admin_user_id}")
            return True
            
        except Exception as e:
            print(f"✗ Login failed: {str(e)}")
            return False

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make authenticated API request"""
        url = f"{self.base_url}/api/admin{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        print(f"\n[{method}] {url}")
        if data:
            print(f"Payload: {data}")
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=self.timeout)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=self.timeout)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=self.timeout)
            else:
                print(f"✗ Unsupported method: {method}")
                return None
            
            print(f"Status: {response.status_code}")
            result = response.json()
            print(f"Response: {result}")
            return result
            
        except Exception as e:
            print(f"✗ Request failed: {str(e)}")
            return None

    def test_list_users(self, limit: int = 10, offset: int = 0) -> bool:
        """Test GET /api/admin/users"""
        print("\n" + "="*60)
        print("TEST: List all users")
        print("="*60)
        
        endpoint = f"/users?limit={limit}&offset={offset}"
        result = self._make_request("GET", endpoint)
        return result is not None and result.get('success')

    def test_get_user_stats(self) -> bool:
        """Test GET /api/admin/users/stats"""
        print("\n" + "="*60)
        print("TEST: Get user statistics")
        print("="*60)
        
        result = self._make_request("GET", "/users/stats")
        return result is not None and result.get('success')

    def test_get_single_user(self, user_id: int) -> bool:
        """Test GET /api/admin/users/{user_id}"""
        print("\n" + "="*60)
        print(f"TEST: Get single user (ID: {user_id})")
        print("="*60)
        
        endpoint = f"/users/{user_id}"
        result = self._make_request("GET", endpoint)
        return result is not None and result.get('success')

    def test_update_user_status(self, user_id: int, is_active: bool) -> bool:
        """Test PUT /api/admin/users/{user_id}"""
        print("\n" + "="*60)
        print(f"TEST: Update user status (ID: {user_id}, active: {is_active})")
        print("="*60)
        
        endpoint = f"/users/{user_id}"
        data = {"is_active": is_active}
        result = self._make_request("PUT", endpoint, data)
        return result is not None and result.get('success')

    def test_update_admin_status(self, user_id: int, is_admin: bool) -> bool:
        """Test PUT /api/admin/users/{user_id}/admin"""
        print("\n" + "="*60)
        print(f"TEST: Update admin status (ID: {user_id}, admin: {is_admin})")
        print("="*60)
        
        endpoint = f"/users/{user_id}/admin"
        data = {"is_admin": is_admin}
        result = self._make_request("PUT", endpoint, data)
        return result is not None and result.get('success')

    def test_get_user_progress(self, user_id: int) -> bool:
        """Test GET /api/admin/users/{user_id}/progress"""
        print("\n" + "="*60)
        print(f"TEST: Get user progress (ID: {user_id})")
        print("="*60)
        
        endpoint = f"/users/{user_id}/progress"
        result = self._make_request("GET", endpoint)
        return result is not None and result.get('success')

    def run_all_tests(self) -> int:
        """Run all admin API tests"""
        if not self.login():
            print("\n✗ Cannot proceed without login")
            return 1
        
        tests_passed = 0
        tests_total = 0
        
        # Test list users
        tests_total += 1
        if self.test_list_users():
            tests_passed += 1
            print("✓ PASS")
        else:
            print("✗ FAIL")
        
        # Test user stats
        tests_total += 1
        if self.test_get_user_stats():
            tests_passed += 1
            print("✓ PASS")
        else:
            print("✗ FAIL")
        
        # Test get admin user
        tests_total += 1
        if self.test_get_single_user(self.admin_user_id):
            tests_passed += 1
            print("✓ PASS")
        else:
            print("✗ FAIL")
        
        # Test user progress
        tests_total += 1
        if self.test_get_user_progress(self.admin_user_id):
            tests_passed += 1
            print("✓ PASS")
        else:
            print("✗ FAIL")
        
        # Print summary
        print("\n" + "="*60)
        print(f"TEST SUMMARY: {tests_passed}/{tests_total} passed")
        print("="*60)
        
        return 0 if tests_passed == tests_total else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Test Bible Quiz admin APIs")
    parser.add_argument("--base-url", default="https://bibel-quiz.onrender.com",
                        help="Base API URL (default: https://bibel-quiz.onrender.com)")
    parser.add_argument("--username", default="admin",
                        help="Admin username (default: admin)")
    parser.add_argument("--password", required=True,
                        help="Admin password (required)")
    parser.add_argument("--user-id", type=int, help="Specific user ID to test")
    parser.add_argument("--timeout", type=int, default=15,
                        help="Request timeout in seconds (default: 15)")
    
    args = parser.parse_args()
    
    tester = AdminAPITester(
        base_url=args.base_url,
        admin_username=args.username,
        admin_password=args.password,
        timeout=args.timeout
    )
    
    return tester.run_all_tests()


if __name__ == "__main__":
    sys.exit(main())
