#!/usr/bin/env python3

import requests
import sys
import json
import io
from datetime import datetime

class CartoMappingAPITester:
    def __init__(self, base_url="https://1faade9b-ecad-41a3-8924-0a760fe670a9.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.client_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.client_user_id = None
        self.service_id = None
        self.order_id = None
        self.uploaded_files = []  # Track uploaded files for testing

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
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
                    response = requests.post(url, data=data, files=files, headers=test_headers)
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

    def test_file_upload_with_notes(self):
        """Test file upload to order with notes - NEW FEATURE"""
        if not self.client_token or not self.order_id:
            print("❌ Cannot test file upload - missing client token or order ID")
            return False
            
        # Create a dummy file for testing
        test_file_content = b"This is a test cartography file content for BMW 320d"
        test_file = io.BytesIO(test_file_content)
        test_notes = "Vehicle: BMW 320d 2018, Current: Stock, Requested: Stage 1 tuning, remove EGR"
        
        headers = {'Authorization': f'Bearer {self.client_token}'}
        files = {'file': ('test_cartography.bin', test_file, 'application/octet-stream')}
        form_data = {'notes': test_notes}
        
        success, response = self.run_test(
            "Upload File with Notes (NEW FEATURE)",
            "POST",
            f"orders/{self.order_id}/upload",
            200,
            data=form_data,
            headers=headers,
            files=files
        )
        
        if success and 'file_id' in response:
            self.uploaded_files.append({
                'file_id': response['file_id'],
                'filename': 'test_cartography.bin',
                'version_type': 'original',
                'notes': test_notes
            })
            print(f"   ✅ File uploaded with notes: {response.get('notes', 'No notes')}")
        
        return success

    def test_file_download(self):
        """Test file download from order with file_id - UPDATED FEATURE"""
        if not self.client_token or not self.order_id or not self.uploaded_files:
            print("❌ Cannot test file download - missing client token, order ID, or uploaded files")
            return False
            
        file_info = self.uploaded_files[0]  # Use first uploaded file
        headers = {'Authorization': f'Bearer {self.client_token}'}
        success, response = self.run_test(
            "Download File with file_id (UPDATED FEATURE)",
            "GET",
            f"orders/{self.order_id}/download/{file_info['file_id']}",
            200,
            headers=headers
        )
        return success

    def test_admin_download_original_file(self):
        """Test admin downloading original client file - NEW FEATURE"""
        if not self.admin_token or not self.order_id or not self.uploaded_files:
            print("❌ Cannot test admin download - missing admin token, order ID, or uploaded files")
            return False
            
        file_info = self.uploaded_files[0]  # Use first uploaded file
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success, response = self.run_test(
            "Admin Download Original File (NEW FEATURE)",
            "GET",
            f"admin/orders/{self.order_id}/download/{file_info['file_id']}",
            200,
            headers=headers
        )
        return success

    def test_admin_upload_versioned_file(self):
        """Test admin uploading versioned file - NEW FEATURE"""
        if not self.admin_token or not self.order_id:
            print("❌ Cannot test admin upload - missing admin token or order ID")
            return False
            
        # Create a modified test file
        modified_file_content = b"This is a MODIFIED cartography file - Stage 1 tuning applied"
        modified_file = io.BytesIO(modified_file_content)
        admin_notes = "Applied Stage 1 tuning, increased boost pressure, optimized fuel mapping"
        version_type = "v1"
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        files = {'file': ('modified_cartography_v1.bin', modified_file, 'application/octet-stream')}
        form_data = {
            'version_type': version_type,
            'notes': admin_notes
        }
        
        success, response = self.run_test(
            "Admin Upload Versioned File (NEW FEATURE)",
            "POST",
            f"admin/orders/{self.order_id}/upload",
            200,
            data=form_data,
            headers=headers,
            files=files
        )
        
        if success and 'file_id' in response:
            self.uploaded_files.append({
                'file_id': response['file_id'],
                'filename': 'modified_cartography_v1.bin',
                'version_type': version_type,
                'notes': admin_notes
            })
            print(f"   ✅ Admin uploaded version: {response.get('version_type', 'Unknown')}")
        
        return success

    def test_admin_upload_multiple_versions(self):
        """Test admin uploading multiple versions - NEW FEATURE"""
        if not self.admin_token or not self.order_id:
            print("❌ Cannot test multiple versions - missing admin token or order ID")
            return False
        
        versions_to_test = [
            {"version": "v2", "notes": "Version 2 - Further optimizations applied"},
            {"version": "sav", "notes": "SAV version - Customer service backup"}
        ]
        
        success_count = 0
        for version_info in versions_to_test:
            file_content = f"Modified cartography file - {version_info['version']} - {version_info['notes']}".encode()
            test_file = io.BytesIO(file_content)
            filename = f"cartography_{version_info['version']}.bin"
            
            headers = {'Authorization': f'Bearer {self.admin_token}'}
            files = {'file': (filename, test_file, 'application/octet-stream')}
            form_data = {
                'version_type': version_info['version'],
                'notes': version_info['notes']
            }
            
            success, response = self.run_test(
                f"Admin Upload {version_info['version'].upper()} Version",
                "POST",
                f"admin/orders/{self.order_id}/upload",
                200,
                data=form_data,
                headers=headers,
                files=files
            )
            
            if success and 'file_id' in response:
                success_count += 1
                self.uploaded_files.append({
                    'file_id': response['file_id'],
                    'filename': filename,
                    'version_type': version_info['version'],
                    'notes': version_info['notes']
                })
        
        print(f"   📊 Successfully uploaded {success_count}/{len(versions_to_test)} versions")
        return success_count == len(versions_to_test)

    def test_get_order_with_all_files(self):
        """Test getting order with all files and versions - ENHANCED FEATURE"""
        if not self.client_token:
            print("❌ Cannot test get orders - missing client token")
            return False
            
        headers = {'Authorization': f'Bearer {self.client_token}'}
        success, response = self.run_test(
            "Get Order with All Files (ENHANCED FEATURE)",
            "GET",
            "orders",
            200,
            headers=headers
        )
        
        if success and isinstance(response, list) and len(response) > 0:
            test_order = None
            for order in response:
                if order['id'] == self.order_id:
                    test_order = order
                    break
            
            if test_order:
                files_info = test_order.get('files', [])
                print(f"   📁 Found {len(files_info)} files in order:")
                for file_info in files_info:
                    print(f"      - {file_info.get('version_type', 'unknown')}: {file_info.get('filename', 'unknown')}")
                    if file_info.get('notes'):
                        print(f"        Notes: {file_info['notes'][:50]}...")
                
                # Check if client_notes are present
                if test_order.get('client_notes'):
                    print(f"   📝 Client notes found: {test_order['client_notes'][:50]}...")
                
                return len(files_info) > 0
        
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

    def test_admin_create_user(self):
        """Test admin creating a new user - NEW FEATURE"""
        if not self.admin_token:
            print("❌ Cannot test admin create user - missing admin token")
            return False
            
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "email": f"admin_created_user_{timestamp}@example.com",
            "password": "AdminCreated123!",
            "first_name": "Admin",
            "last_name": "Created",
            "phone": "0987654321",
            "company": "Admin Created Company",
            "role": "client"
        }
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success, response = self.run_test(
            "Admin Create User (NEW FEATURE)",
            "POST",
            "admin/users",
            200,
            data=user_data,
            headers=headers
        )
        
        if success and 'id' in response:
            self.created_user_id = response['id']
            print(f"   ✅ Created user with ID: {self.created_user_id}")
        
        return success

    def test_admin_update_user(self):
        """Test admin updating a user - NEW FEATURE"""
        if not self.admin_token or not hasattr(self, 'created_user_id'):
            print("❌ Cannot test admin update user - missing admin token or created user ID")
            return False
            
        update_data = {
            "first_name": "Updated",
            "last_name": "User",
            "company": "Updated Company",
            "is_active": False  # Test deactivating user
        }
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success, response = self.run_test(
            "Admin Update User (NEW FEATURE)",
            "PUT",
            f"admin/users/{self.created_user_id}",
            200,
            data=update_data,
            headers=headers
        )
        
        if success:
            print(f"   ✅ Updated user - Active status: {response.get('is_active', 'Unknown')}")
        
        return success

    def test_admin_delete_user(self):
        """Test admin deleting a user - NEW FEATURE"""
        if not self.admin_token or not hasattr(self, 'created_user_id'):
            print("❌ Cannot test admin delete user - missing admin token or created user ID")
            return False
            
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success, response = self.run_test(
            "Admin Delete User (NEW FEATURE)",
            "DELETE",
            f"admin/users/{self.created_user_id}",
            200,
            headers=headers
        )
        
        if success:
            print(f"   ✅ User deleted successfully")
        
        return success

    def test_admin_get_all_services(self):
        """Test admin getting all services (including inactive) - NEW FEATURE"""
        if not self.admin_token:
            print("❌ Cannot test admin get services - missing admin token")
            return False
            
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success, response = self.run_test(
            "Admin Get All Services (NEW FEATURE)",
            "GET",
            "admin/services",
            200,
            headers=headers
        )
        
        if success and isinstance(response, list):
            active_count = sum(1 for service in response if service.get('is_active', True))
            inactive_count = len(response) - active_count
            print(f"   📊 Found {len(response)} total services ({active_count} active, {inactive_count} inactive)")
        
        return success

    def test_admin_create_service(self):
        """Test admin creating a new service - NEW FEATURE"""
        if not self.admin_token:
            print("❌ Cannot test admin create service - missing admin token")
            return False
            
        timestamp = datetime.now().strftime('%H%M%S')
        service_data = {
            "name": f"Test Service {timestamp}",
            "price": 150.0,
            "description": "Test service created by admin for testing purposes",
            "is_active": True
        }
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success, response = self.run_test(
            "Admin Create Service (NEW FEATURE)",
            "POST",
            "admin/services",
            200,
            data=service_data,
            headers=headers
        )
        
        if success and 'id' in response:
            self.created_service_id = response['id']
            print(f"   ✅ Created service with ID: {self.created_service_id}, Price: {response.get('price', 'Unknown')}€")
        
        return success

    def test_admin_update_service(self):
        """Test admin updating a service - NEW FEATURE"""
        if not self.admin_token or not hasattr(self, 'created_service_id'):
            print("❌ Cannot test admin update service - missing admin token or created service ID")
            return False
            
        update_data = {
            "name": "Updated Test Service",
            "price": 200.0,
            "description": "Updated service description with new pricing",
            "is_active": False  # Test deactivating service
        }
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success, response = self.run_test(
            "Admin Update Service (NEW FEATURE)",
            "PUT",
            f"admin/services/{self.created_service_id}",
            200,
            data=update_data,
            headers=headers
        )
        
        if success:
            print(f"   ✅ Updated service - Price: {response.get('price', 'Unknown')}€, Active: {response.get('is_active', 'Unknown')}")
        
        return success

    def test_admin_delete_service(self):
        """Test admin deleting a service - NEW FEATURE"""
        if not self.admin_token or not hasattr(self, 'created_service_id'):
            print("❌ Cannot test admin delete service - missing admin token or created service ID")
            return False
            
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success, response = self.run_test(
            "Admin Delete Service (NEW FEATURE)",
            "DELETE",
            f"admin/services/{self.created_service_id}",
            200,
            headers=headers
        )
        
        if success:
            print(f"   ✅ Service deleted successfully")
        
        return success

    def test_inactive_service_not_in_public_list(self):
        """Test that inactive services don't appear in public service list - NEW FEATURE"""
        # First get public services (should only show active)
        success_public, public_response = self.run_test(
            "Get Public Services (Active Only)",
            "GET",
            "services",
            200
        )
        
        if not success_public:
            return False
            
        # Then get admin services (should show all)
        if not self.admin_token:
            print("❌ Cannot test admin services - missing admin token")
            return False
            
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success_admin, admin_response = self.run_test(
            "Get Admin Services (All Services)",
            "GET",
            "admin/services",
            200,
            headers=headers
        )
        
        if success_admin and isinstance(public_response, list) and isinstance(admin_response, list):
            public_count = len(public_response)
            admin_count = len(admin_response)
            inactive_count = sum(1 for service in admin_response if not service.get('is_active', True))
            
            print(f"   📊 Public services: {public_count}, Admin services: {admin_count}, Inactive: {inactive_count}")
            
            # Verify that public list has fewer or equal services than admin list
            if public_count <= admin_count:
                print(f"   ✅ Service visibility working correctly")
                return True
            else:
                print(f"   ❌ Public list has more services than admin list - this shouldn't happen")
                return False
        
        return success_admin

def main():
    print("🚀 Starting CartoMapping API Tests - NEW FEATURES TESTING")
    print("=" * 60)
    
    tester = CartoMappingAPITester()
    
    # Test sequence - including NEW FEATURES
    tests = [
        # Basic authentication and setup
        ("Admin Authentication", tester.test_admin_login),
        ("Client Registration & Login", tester.test_client_registration),
        ("Get Current User (Admin)", lambda: tester.test_get_current_user(tester.admin_token, "admin")),
        ("Get Current User (Client)", lambda: tester.test_get_current_user(tester.client_token, "client")),
        ("Get Services", tester.test_get_services),
        ("Create Order", tester.test_create_order),
        
        # NEW FEATURES TESTING
        ("🆕 Upload File with Notes", tester.test_file_upload_with_notes),
        ("🆕 Download File with file_id", tester.test_file_download),
        ("🆕 Admin Download Original File", tester.test_admin_download_original_file),
        ("🆕 Admin Upload Versioned File", tester.test_admin_upload_versioned_file),
        ("🆕 Admin Upload Multiple Versions", tester.test_admin_upload_multiple_versions),
        ("🆕 Get Order with All Files", tester.test_get_order_with_all_files),
        
        # Admin functionality
        ("Admin Get Users", tester.test_admin_get_users),
        ("Admin Get Orders", tester.test_admin_get_orders),
        ("Admin Update Order Status", tester.test_admin_update_order_status),
        
        # Security tests
        ("Unauthorized Access", tester.test_unauthorized_access),
        ("Admin-Only Access Control", tester.test_admin_only_access),
    ]
    
    print("\n🔧 BASIC FUNCTIONALITY TESTS:")
    print("-" * 40)
    basic_tests = tests[:6]
    for test_name, test_func in basic_tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
    
    print("\n🆕 NEW FEATURES TESTS:")
    print("-" * 40)
    new_feature_tests = tests[6:12]
    for test_name, test_func in new_feature_tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
    
    print("\n🔒 ADMIN & SECURITY TESTS:")
    print("-" * 40)
    admin_tests = tests[12:]
    for test_name, test_func in admin_tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
    
    # Print final results
    print(f"\n{'='*60}")
    print(f"📊 FINAL RESULTS")
    print(f"{'='*60}")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    # Show uploaded files summary
    if tester.uploaded_files:
        print(f"\n📁 FILES CREATED DURING TESTING:")
        for file_info in tester.uploaded_files:
            print(f"  - {file_info['version_type']}: {file_info['filename']} (ID: {file_info['file_id']})")
            if file_info.get('notes'):
                print(f"    Notes: {file_info['notes'][:60]}...")
    
    if tester.tests_passed == tester.tests_run:
        print("\n🎉 All tests passed! NEW FEATURES working correctly!")
        return 0
    else:
        print(f"\n⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())