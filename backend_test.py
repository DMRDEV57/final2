#!/usr/bin/env python3

import requests
import sys
import json
import io
from datetime import datetime

class CartoMappingAPITester:
    def __init__(self, base_url="https://1faade9b-ecad-41a3-8924-0a760fe670a9.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.client_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.client_user_id = None
        self.service_id = None
        self.order_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                if files:
                    # Remove Content-Type for file uploads
                    test_headers.pop('Content-Type', None)
                    response = requests.post(url, files=files, headers=test_headers)
                else:
                    response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_admin_login(self):
        """Test admin login"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@cartomapping.com", "password": "admin123"}
        )
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            return True
        return False

    def test_client_registration(self):
        """Test client registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        client_data = {
            "email": f"test_client_{timestamp}@example.com",
            "password": "TestPass123!",
            "first_name": "Test",
            "last_name": "Client",
            "phone": "0123456789",
            "company": "Test Company"
        }
        
        success, response = self.run_test(
            "Client Registration",
            "POST",
            "auth/register",
            200,
            data=client_data
        )
        if success and 'id' in response:
            self.client_user_id = response['id']
            # Now login with the new client
            login_success, login_response = self.run_test(
                "Client Login",
                "POST",
                "auth/login",
                200,
                data={"email": client_data["email"], "password": client_data["password"]}
            )
            if login_success and 'access_token' in login_response:
                self.client_token = login_response['access_token']
                return True
        return False

    def test_get_current_user(self, token, user_type):
        """Test getting current user info"""
        headers = {'Authorization': f'Bearer {token}'}
        success, response = self.run_test(
            f"Get Current User ({user_type})",
            "GET",
            "auth/me",
            200,
            headers=headers
        )
        return success

    def test_get_services(self):
        """Test getting available services"""
        success, response = self.run_test(
            "Get Services",
            "GET",
            "services",
            200
        )
        if success and len(response) > 0:
            self.service_id = response[0]['id']  # Store first service ID for order testing
            print(f"   Found {len(response)} services")
            return True
        return False

    def test_create_order(self):
        """Test creating an order"""
        if not self.client_token or not self.service_id:
            print("❌ Cannot test order creation - missing client token or service ID")
            return False
            
        headers = {'Authorization': f'Bearer {self.client_token}'}
        success, response = self.run_test(
            "Create Order",
            "POST",
            "orders",
            200,
            data={"service_id": self.service_id},
            headers=headers
        )
        if success and 'id' in response:
            self.order_id = response['id']
            return True
        return False

    def test_get_user_orders(self):
        """Test getting user orders"""
        if not self.client_token:
            print("❌ Cannot test get orders - missing client token")
            return False
            
        headers = {'Authorization': f'Bearer {self.client_token}'}
        success, response = self.run_test(
            "Get User Orders",
            "GET",
            "orders",
            200,
            headers=headers
        )
        return success

    def test_file_upload(self):
        """Test file upload to order"""
        if not self.client_token or not self.order_id:
            print("❌ Cannot test file upload - missing client token or order ID")
            return False
            
        # Create a dummy file for testing
        test_file_content = b"This is a test cartography file content"
        test_file = io.BytesIO(test_file_content)
        
        headers = {'Authorization': f'Bearer {self.client_token}'}
        files = {'file': ('test_cartography.bin', test_file, 'application/octet-stream')}
        
        success, response = self.run_test(
            "Upload File to Order",
            "POST",
            f"orders/{self.order_id}/upload",
            200,
            headers=headers,
            files=files
        )
        return success

    def test_file_download(self):
        """Test file download from order"""
        if not self.client_token or not self.order_id:
            print("❌ Cannot test file download - missing client token or order ID")
            return False
            
        headers = {'Authorization': f'Bearer {self.client_token}'}
        success, response = self.run_test(
            "Download File from Order",
            "GET",
            f"orders/{self.order_id}/download",
            200,
            headers=headers
        )
        return success

    def test_admin_get_users(self):
        """Test admin getting all users"""
        if not self.admin_token:
            print("❌ Cannot test admin get users - missing admin token")
            return False
            
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success, response = self.run_test(
            "Admin Get All Users",
            "GET",
            "admin/users",
            200,
            headers=headers
        )
        return success

    def test_admin_get_orders(self):
        """Test admin getting all orders"""
        if not self.admin_token:
            print("❌ Cannot test admin get orders - missing admin token")
            return False
            
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success, response = self.run_test(
            "Admin Get All Orders",
            "GET",
            "admin/orders",
            200,
            headers=headers
        )
        return success

    def test_admin_update_order_status(self):
        """Test admin updating order status"""
        if not self.admin_token or not self.order_id:
            print("❌ Cannot test admin update order - missing admin token or order ID")
            return False
            
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success, response = self.run_test(
            "Admin Update Order Status",
            "PUT",
            f"admin/orders/{self.order_id}/status",
            200,
            data={"status": "completed"},
            headers=headers
        )
        return success

    def test_unauthorized_access(self):
        """Test unauthorized access to protected endpoints"""
        success, response = self.run_test(
            "Unauthorized Access to Protected Endpoint",
            "GET",
            "auth/me",
            401
        )
        return success

    def test_admin_only_access(self):
        """Test client trying to access admin endpoints"""
        if not self.client_token:
            print("❌ Cannot test admin-only access - missing client token")
            return False
            
        headers = {'Authorization': f'Bearer {self.client_token}'}
        success, response = self.run_test(
            "Client Access to Admin Endpoint (Should Fail)",
            "GET",
            "admin/users",
            403,
            headers=headers
        )
        return success

def main():
    print("🚀 Starting CartoMapping API Tests")
    print("=" * 50)
    
    tester = CartoMappingAPITester()
    
    # Test sequence
    tests = [
        ("Admin Authentication", tester.test_admin_login),
        ("Client Registration & Login", tester.test_client_registration),
        ("Get Current User (Admin)", lambda: tester.test_get_current_user(tester.admin_token, "admin")),
        ("Get Current User (Client)", lambda: tester.test_get_current_user(tester.client_token, "client")),
        ("Get Services", tester.test_get_services),
        ("Create Order", tester.test_create_order),
        ("Get User Orders", tester.test_get_user_orders),
        ("Upload File", tester.test_file_upload),
        ("Download File", tester.test_file_download),
        ("Admin Get Users", tester.test_admin_get_users),
        ("Admin Get Orders", tester.test_admin_get_orders),
        ("Admin Update Order Status", tester.test_admin_update_order_status),
        ("Unauthorized Access", tester.test_unauthorized_access),
        ("Admin-Only Access Control", tester.test_admin_only_access),
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
    
    # Print final results
    print(f"\n{'='*50}")
    print(f"📊 FINAL RESULTS")
    print(f"{'='*50}")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())