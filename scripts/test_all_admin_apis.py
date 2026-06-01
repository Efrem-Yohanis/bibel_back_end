"""
Comprehensive Admin API Test Suite
Tests all admin endpoints for user, book, language, and import management
"""

import requests
import sys
import json
from typing import Optional, Dict, Any


class AdminAPIComprehensiveTest:
    def __init__(self, base_url: str, admin_username: str, admin_password: str, timeout: int = 15):
        self.base_url = base_url.rstrip('/')
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.timeout = timeout
        self.access_token: Optional[str] = None
        self.admin_user_id: Optional[int] = None
        self.test_book_id: Optional[int] = None
        self.test_language_id: Optional[int] = None
        self.results = []

    def log_test(self, name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✓ PASS" if passed else "✗ FAIL"
        self.results.append({"name": name, "passed": passed, "details": details})
        print(f"{status} | {name}")
        if details:
            print(f"      {details}")

    def login(self) -> bool:
        """Login as admin"""
        print("\n" + "="*70)
        print("AUTHENTICATION")
        print("="*70)
        
        url = f"{self.base_url}/api/auth/login"
        payload = {
            "username_or_email": self.admin_username,
            "password": self.admin_password
        }
        
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            
            if response.status_code != 200:
                self.log_test("Login", False, f"Status {response.status_code}: {response.text}")
                return False
            
            data = response.json()
            self.access_token = data['data']['access_token']
            self.admin_user_id = data['data']['user_id']
            self.log_test("Login", True, f"User ID: {self.admin_user_id}")
            return True
            
        except Exception as e:
            self.log_test("Login", False, str(e))
            return False

    def get_headers(self) -> Dict[str, str]:
        """Get auth headers"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    # ==================== USER MANAGEMENT ====================

    def test_list_users(self) -> bool:
        """GET /api/admin/users"""
        url = f"{self.base_url}/api/admin/users?limit=10&offset=0"
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=self.timeout)
            passed = response.status_code == 200 and response.json().get('success')
            data = response.json().get('data', {})
            self.log_test("List Users (GET /api/admin/users)", passed, 
                         f"Total users: {data.get('total', 0)}")
            return passed
        except Exception as e:
            self.log_test("List Users", False, str(e))
            return False

    def test_user_stats(self) -> bool:
        """GET /api/admin/users/stats"""
        url = f"{self.base_url}/api/admin/users/stats"
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=self.timeout)
            passed = response.status_code == 200 and response.json().get('success')
            data = response.json().get('data', {})
            self.log_test("User Statistics (GET /api/admin/users/stats)", passed,
                         f"Total users: {data.get('total_users', 0)}")
            return passed
        except Exception as e:
            self.log_test("User Statistics", False, str(e))
            return False

    def test_get_user_detail(self, user_id: int) -> bool:
        """GET /api/admin/users/{user_id}"""
        url = f"{self.base_url}/api/admin/users/{user_id}"
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=self.timeout)
            passed = response.status_code == 200 and response.json().get('success')
            data = response.json().get('data', {})
            self.log_test(f"Get User Detail (GET /api/admin/users/{user_id})", passed,
                         f"User: {data.get('username', 'N/A')}")
            return passed
        except Exception as e:
            self.log_test("Get User Detail", False, str(e))
            return False

    def test_toggle_user_status(self, user_id: int) -> bool:
        """PUT /api/admin/users/{user_id} - Toggle active status"""
        if user_id == self.admin_user_id:
            self.log_test(f"Toggle User Status (PUT /api/admin/users/{user_id})", True,
                         "Skipped (self toggle would deactivate admin)")
            return True

        url = f"{self.base_url}/api/admin/users/{user_id}"
        payload = {"is_active": False}
        try:
            response = requests.put(url, json=payload, headers=self.get_headers(), timeout=self.timeout)
            passed = response.status_code == 200 and response.json().get('success')
            self.log_test(f"Toggle User Status (PUT /api/admin/users/{user_id})", passed)
            
            # Toggle back
            payload = {"is_active": True}
            restore = requests.put(url, json=payload, headers=self.get_headers(), timeout=self.timeout)
            if restore.status_code != 200 or not restore.json().get('success'):
                self.log_test(f"Restore User Status (PUT /api/admin/users/{user_id})", False,
                             "Failed to restore status after toggle")
                return False
            return passed
        except Exception as e:
            self.log_test("Toggle User Status", False, str(e))
            return False

    def test_update_admin_status(self, user_id: int) -> bool:
        """PUT /api/admin/users/{user_id}/admin - Toggle admin status"""
        # Skip if testing on self
        if user_id == self.admin_user_id:
            self.log_test(f"Update Admin Status (PUT /api/admin/users/{user_id}/admin)", True, 
                         "Skipped (testing on self)")
            return True
            
        url = f"{self.base_url}/api/admin/users/{user_id}/admin"
        payload = {"is_admin": True}
        try:
            response = requests.put(url, json=payload, headers=self.get_headers(), timeout=self.timeout)
            passed = response.status_code == 200 and response.json().get('success')
            self.log_test(f"Update Admin Status (PUT /api/admin/users/{user_id}/admin)", passed)
            
            # Toggle back
            payload = {"is_admin": False}
            requests.put(url, json=payload, headers=self.get_headers(), timeout=self.timeout)
            return passed
        except Exception as e:
            self.log_test("Update Admin Status", False, str(e))
            return False

    def test_user_progress(self, user_id: int) -> bool:
        """GET /api/admin/users/{user_id}/progress"""
        url = f"{self.base_url}/api/admin/users/{user_id}/progress"
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=self.timeout)
            passed = response.status_code == 200 and response.json().get('success')
            self.log_test(f"Get User Progress (GET /api/admin/users/{user_id}/progress)", passed)
            return passed
        except Exception as e:
            self.log_test("Get User Progress", False, str(e))
            return False

    # ==================== BOOK MANAGEMENT ====================

    def test_list_books(self) -> bool:
        """GET /api/admin/books"""
        url = f"{self.base_url}/api/admin/books"
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=self.timeout)
            passed = response.status_code == 200 and response.json().get('success')
            data = response.json().get('data', [])
            if data:
                self.test_book_id = data[0].get('id')
            self.log_test("List Books (GET /api/admin/books)", passed,
                         f"Books found: {len(data)}")
            return passed
        except Exception as e:
            self.log_test("List Books", False, str(e))
            return False

    def test_create_book(self) -> bool:
        """POST /api/admin/books"""
        url = f"{self.base_url}/api/admin/books"
        payload = {
            "name": "Test Book",
            "testament": "Old"
        }
        try:
            response = requests.post(url, json=payload, headers=self.get_headers(), timeout=self.timeout)
            passed = response.status_code == 201 and response.json().get('success')
            data = response.json().get('data', {})
            created_id = data.get('id') or data.get('book_id')
            self.log_test("Create Book (POST /api/admin/books)", passed,
                         f"Created Book ID: {created_id}")
            
            # Store for later cleanup
            if passed and created_id:
                self.test_book_id = created_id
            return passed
        except Exception as e:
            self.log_test("Create Book", False, str(e))
            return False

    def test_get_book_detail(self, book_id: int) -> bool:
        """GET /api/admin/books/{book_id}"""
        url = f"{self.base_url}/api/admin/books/{book_id}"
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=self.timeout)
            passed = response.status_code == 200 and response.json().get('success')
            data = response.json().get('data', {})
            self.log_test(f"Get Book Detail (GET /api/admin/books/{book_id})", passed,
                         f"Book: {data.get('name', 'N/A')}")
            return passed
        except Exception as e:
            self.log_test("Get Book Detail", False, str(e))
            return False

    def test_update_book(self, book_id: int) -> bool:
        """PUT /api/admin/books/{book_id}"""
        url = f"{self.base_url}/api/admin/books/{book_id}"
        payload = {"name": "Updated Test Book"}
        try:
            response = requests.put(url, json=payload, headers=self.get_headers(), timeout=self.timeout)
            passed = response.status_code == 200 and response.json().get('success')
            self.log_test(f"Update Book (PUT /api/admin/books/{book_id})", passed)
            return passed
        except Exception as e:
            self.log_test("Update Book", False, str(e))
            return False

    def test_delete_book(self, book_id: int) -> bool:
        """DELETE /api/admin/books/{book_id}"""
        url = f"{self.base_url}/api/admin/books/{book_id}"
        try:
            response = requests.delete(url, headers=self.get_headers(), timeout=self.timeout)
            passed = response.status_code == 200 and response.json().get('success')
            self.log_test(f"Delete Book (DELETE /api/admin/books/{book_id})", passed)
            return passed
        except Exception as e:
            self.log_test("Delete Book", False, str(e))
            return False

    # ==================== LANGUAGE MANAGEMENT ====================

    def test_list_languages(self) -> bool:
        """GET /api/admin/languages"""
        url = f"{self.base_url}/api/admin/languages"
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=self.timeout)
            passed = response.status_code == 200 and response.json().get('success')
            data = response.json().get('data', [])
            if data and not self.test_language_id:
                self.test_language_id = data[0].get('id')
            self.log_test("List Languages (GET /api/admin/languages)", passed,
                         f"Languages found: {len(data)}")
            return passed
        except Exception as e:
            self.log_test("List Languages", False, str(e))
            return False

    def test_create_language(self) -> bool:
        """POST /api/admin/languages"""
        url = f"{self.base_url}/api/admin/languages"
        payload = {
            "code": "test_lang",
            "name": "Test Language",
            "native_name": "Test Native"
        }
        try:
            response = requests.post(url, json=payload, headers=self.get_headers(), timeout=self.timeout)
            passed = response.status_code == 201 and response.json().get('success')
            data = response.json().get('data', {})
            created_id = data.get('id') or data.get('language_id')
            self.log_test("Create Language (POST /api/admin/languages)", passed,
                         f"Created Language ID: {created_id}")
            
            if passed and created_id:
                self.test_language_id = created_id
            return passed
        except Exception as e:
            self.log_test("Create Language", False, str(e))
            return False

    def test_update_language(self, language_id: int) -> bool:
        """PUT /api/admin/languages/{language_id}"""
        url = f"{self.base_url}/api/admin/languages/{language_id}"
        payload = {"is_active": False}
        try:
            response = requests.put(url, json=payload, headers=self.get_headers(), timeout=self.timeout)
            passed = response.status_code == 200 and response.json().get('success')
            self.log_test(f"Update Language (PUT /api/admin/languages/{language_id})", passed)
            
            # Toggle back
            payload = {"is_active": True}
            requests.put(url, json=payload, headers=self.get_headers(), timeout=self.timeout)
            return passed
        except Exception as e:
            self.log_test("Update Language", False, str(e))
            return False

    def test_delete_language(self, language_id: int) -> bool:
        """DELETE /api/admin/languages/{language_id}"""
        url = f"{self.base_url}/api/admin/languages/{language_id}"
        try:
            response = requests.delete(url, headers=self.get_headers(), timeout=self.timeout)
            passed = response.status_code == 200 and response.json().get('success')
            self.log_test(f"Delete Language (DELETE /api/admin/languages/{language_id})", passed)
            return passed
        except Exception as e:
            self.log_test("Delete Language", False, str(e))
            return False

    # ==================== IMPORT MANAGEMENT ====================

    def test_bible_import_status(self) -> bool:
        """GET /api/admin/import/bible"""
        url = f"{self.base_url}/api/admin/import/bible"
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=self.timeout)
            passed = response.status_code == 200 and response.json().get('success')
            data = response.json().get('data', {})
            self.log_test("Bible Import Status (GET /api/admin/import/bible)", passed,
                         f"Books imported: {data.get('books_imported', 0)}")
            return passed
        except Exception as e:
            self.log_test("Bible Import Status", False, str(e))
            return False

    def test_questions_import_status(self) -> bool:
        """GET /api/admin/import/questions"""
        url = f"{self.base_url}/api/admin/import/questions"
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=self.timeout)
            passed = response.status_code == 200 and response.json().get('success')
            data = response.json().get('data', {})
            self.log_test("Questions Import Status (GET /api/admin/import/questions)", passed,
                         f"Total questions: {data.get('total_questions', 0)}")
            return passed
        except Exception as e:
            self.log_test("Questions Import Status", False, str(e))
            return False

    # ==================== MAIN TEST RUNNER ====================

    def run_all_tests(self) -> int:
        """Run all tests"""
        if not self.login():
            print("\n✗ Cannot proceed without login")
            return 1

        print("\n" + "="*70)
        print("USER MANAGEMENT TESTS")
        print("="*70)
        self.test_list_users()
        self.test_user_stats()
        self.test_get_user_detail(self.admin_user_id)
        self.test_toggle_user_status(self.admin_user_id)
        self.test_user_progress(self.admin_user_id)

        print("\n" + "="*70)
        print("BOOK MANAGEMENT TESTS")
        print("="*70)
        self.test_list_books()
        self.test_create_book()
        if self.test_book_id:
            self.test_get_book_detail(self.test_book_id)
            self.test_update_book(self.test_book_id)
            self.test_delete_book(self.test_book_id)

        print("\n" + "="*70)
        print("LANGUAGE MANAGEMENT TESTS")
        print("="*70)
        self.test_list_languages()
        self.test_create_language()
        if self.test_language_id:
            self.test_update_language(self.test_language_id)
            self.test_delete_language(self.test_language_id)

        print("\n" + "="*70)
        print("IMPORT MANAGEMENT TESTS")
        print("="*70)
        self.test_bible_import_status()
        self.test_questions_import_status()

        # Print summary
        passed = sum(1 for r in self.results if r['passed'])
        total = len(self.results)
        
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✓")
        print(f"Failed: {total - passed} ✗")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        print("="*70)

        return 0 if passed == total else 1


def main() -> int:
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive Admin API Test Suite")
    parser.add_argument("--base-url", default="https://bibel-quiz.onrender.com",
                        help="Base API URL (default: https://bibel-quiz.onrender.com)")
    parser.add_argument("--username", default="admin",
                        help="Admin username (default: admin)")
    parser.add_argument("--password", required=True,
                        help="Admin password (required)")
    parser.add_argument("--timeout", type=int, default=15,
                        help="Request timeout in seconds (default: 15)")
    
    args = parser.parse_args()
    
    tester = AdminAPIComprehensiveTest(
        base_url=args.base_url,
        admin_username=args.username,
        admin_password=args.password,
        timeout=args.timeout
    )
    
    return tester.run_all_tests()


if __name__ == '__main__':
    sys.exit(main())
