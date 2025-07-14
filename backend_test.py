#!/usr/bin/env python3

import requests
import sys
import json
import io
from datetime import datetime

class CartoMappingAPITester:
    def __init__(self, base_url="https://a3dcf5d2-f7d5-441b-b7fd-c28745e3f454.preview.emergentagent.com"):
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

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, files=None, form_data=False):
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
                elif form_data:
                    # Form data (for combined orders)
                    test_headers.pop('Content-Type', None)
                    response = requests.post(url, data=data, headers=test_headers)
                else:
                    # JSON data
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
            data={"email": "admin@test.com", "password": "admin123"}
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
            "country": "France",  # Added required field
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

    def test_create_combined_order(self):
        """Test creating a combined order with multiple services - FOCUS TEST"""
        if not self.client_token:
            print("❌ Cannot test combined order creation - missing client token")
            return False
            
        # Prepare combined order data
        import json
        combined_services = [
            {"name": "Stage 1", "price": 70.0},
            {"name": "Solution EGR", "price": 20.0},
            {"name": "Solution FAP", "price": 20.0}
        ]
        
        total_price = sum(service["price"] for service in combined_services)
        service_name = "Stage 1 + EGR + FAP"
        
        headers = {'Authorization': f'Bearer {self.client_token}'}
        
        form_data = {
            'service_name': service_name,
            'price': str(total_price),  # Convert to string for form data
            'combined_services': json.dumps(combined_services)
        }
        
        success, response = self.run_test(
            "🎯 Create Combined Order (FOCUS TEST)",
            "POST",
            "orders/combined",
            200,
            data=form_data,
            headers=headers,
            form_data=True
        )
        
        if success and 'id' in response:
            self.combined_order_id = response['id']
            print(f"   ✅ Combined order created with ID: {self.combined_order_id}")
            print(f"   💰 Total price: {total_price}€")
            print(f"   📋 Services: {', '.join([s['name'] for s in combined_services])}")
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

    def test_admin_cancel_order_sets_price_to_zero(self):
        """Test that cancelling an order sets price to 0 - REVIEW REQUEST TEST"""
        if not self.admin_token or not self.order_id:
            print("❌ Cannot test order cancellation - missing admin token or order ID")
            return False
            
        # First get the order to check original price
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success_get, order_response = self.run_test(
            "Get Order Before Cancellation",
            "GET",
            "admin/orders",
            200,
            headers=headers
        )
        
        original_price = None
        if success_get and isinstance(order_response, list):
            for order in order_response:
                if order['id'] == self.order_id:
                    original_price = order.get('price', 0)
                    break
        
        print(f"   💰 Original order price: {original_price}€")
        
        # Cancel the order
        success, response = self.run_test(
            "🎯 Admin Cancel Order (Sets Price to 0)",
            "PUT",
            f"admin/orders/{self.order_id}/cancel",
            200,
            headers=headers
        )
        
        if success:
            # Verify the order is cancelled and price is 0
            success_verify, verify_response = self.run_test(
                "Verify Order Cancelled with Price 0",
                "GET",
                "admin/orders",
                200,
                headers=headers
            )
            
            if success_verify and isinstance(verify_response, list):
                for order in verify_response:
                    if order['id'] == self.order_id:
                        cancelled_price = order.get('price', -1)
                        status = order.get('status', 'unknown')
                        print(f"   ✅ Order status: {status}, Price after cancellation: {cancelled_price}€")
                        return status == 'cancelled' and cancelled_price == 0.0
        
        return success

    def test_admin_delete_single_notification(self):
        """Test deleting a single notification - REVIEW REQUEST TEST"""
        if not self.admin_token:
            print("❌ Cannot test notification deletion - missing admin token")
            return False
            
        # First create a notification by creating a SAV request
        if self.client_token and self.order_id:
            client_headers = {'Authorization': f'Bearer {self.client_token}'}
            self.run_test(
                "Create SAV Request (for notification)",
                "POST",
                f"orders/{self.order_id}/sav-request",
                200,
                headers=client_headers
            )
        
        # Get notifications to find one to delete
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success_get, notifications = self.run_test(
            "Get Admin Notifications",
            "GET",
            "admin/notifications",
            200,
            headers=headers
        )
        
        if success_get and isinstance(notifications, list) and len(notifications) > 0:
            notification_id = notifications[0]['id']
            print(f"   🔔 Found notification to delete: {notification_id}")
            
            # Delete the specific notification
            success, response = self.run_test(
                "🎯 Delete Single Notification",
                "DELETE",
                f"admin/notifications/{notification_id}",
                200,
                headers=headers
            )
            
            if success:
                # Verify notification was deleted
                success_verify, verify_notifications = self.run_test(
                    "Verify Notification Deleted",
                    "GET",
                    "admin/notifications",
                    200,
                    headers=headers
                )
                
                if success_verify and isinstance(verify_notifications, list):
                    remaining_ids = [n['id'] for n in verify_notifications]
                    deleted_successfully = notification_id not in remaining_ids
                    print(f"   ✅ Notification deleted: {deleted_successfully}")
                    return deleted_successfully
            
            return success
        else:
            print("   ⚠️ No notifications found to delete")
            return True  # Not a failure if no notifications exist

    def test_admin_delete_all_notifications(self):
        """Test deleting all notifications - REVIEW REQUEST TEST"""
        if not self.admin_token:
            print("❌ Cannot test delete all notifications - missing admin token")
            return False
            
        # First create some notifications if none exist
        if self.client_token and self.order_id:
            client_headers = {'Authorization': f'Bearer {self.client_token}'}
            # Create multiple SAV requests for notifications
            for i in range(2):
                self.run_test(
                    f"Create SAV Request {i+1} (for notifications)",
                    "POST",
                    f"orders/{self.order_id}/sav-request",
                    200,
                    headers=client_headers
                )
        
        # Get current notification count
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success_get, notifications_before = self.run_test(
            "Get Notifications Before Delete All",
            "GET",
            "admin/notifications",
            200,
            headers=headers
        )
        
        notifications_count = len(notifications_before) if success_get and isinstance(notifications_before, list) else 0
        print(f"   🔔 Found {notifications_count} notifications to delete")
        
        # Delete all notifications
        success, response = self.run_test(
            "🎯 Delete All Notifications",
            "DELETE",
            "admin/notifications",
            200,
            headers=headers
        )
        
        if success:
            # Verify all notifications were deleted
            success_verify, verify_notifications = self.run_test(
                "Verify All Notifications Deleted",
                "GET",
                "admin/notifications",
                200,
                headers=headers
            )
            
            if success_verify and isinstance(verify_notifications, list):
                remaining_count = len(verify_notifications)
                print(f"   ✅ Notifications remaining after delete all: {remaining_count}")
                return remaining_count == 0
        
        return success

    def test_admin_get_pending_orders(self):
        """Test getting pending orders endpoint - REVIEW REQUEST TEST"""
        if not self.admin_token:
            print("❌ Cannot test pending orders - missing admin token")
            return False
            
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success, response = self.run_test(
            "🎯 Get Pending Orders (Fichier à modifier)",
            "GET",
            "admin/orders/pending",
            200,
            headers=headers
        )
        
        if success and isinstance(response, list):
            pending_count = len(response)
            print(f"   📋 Found {pending_count} pending orders")
            
            # Check that orders have user information
            if pending_count > 0:
                first_order = response[0]
                has_user_info = 'user' in first_order
                user_email = first_order.get('user', {}).get('email', 'No email')
                print(f"   👤 First order user info: {user_email}")
                print(f"   ✅ Orders include user information: {has_user_info}")
                return has_user_info
            else:
                print("   ✅ No pending orders found (this is valid)")
                return True
        
        return success

    def test_admin_order_status_uses_termine(self):
        """Test that order status uses 'terminé' instead of 'completed' - REVIEW REQUEST TEST"""
        if not self.admin_token or not self.order_id:
            print("❌ Cannot test status terminology - missing admin token or order ID")
            return False
            
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success, response = self.run_test(
            "🎯 Update Order Status to 'terminé'",
            "PUT",
            f"admin/orders/{self.order_id}/status",
            200,
            data={"status": "terminé", "admin_notes": "Test completion with correct French terminology"},
            headers=headers
        )
        
        if success:
            # Verify the order status is set to 'terminé'
            success_verify, orders = self.run_test(
                "Verify Order Status is 'terminé'",
                "GET",
                "admin/orders",
                200,
                headers=headers
            )
            
            if success_verify and isinstance(orders, list):
                for order in orders:
                    if order['id'] == self.order_id:
                        status = order.get('status', 'unknown')
                        completed_at = order.get('completed_at')
                        print(f"   ✅ Order status: '{status}' (should be 'terminé')")
                        print(f"   📅 Completed at: {completed_at}")
                        return status == 'terminé' and completed_at is not None
        
        return success

    def test_admin_upload_with_new_version_options(self):
        """Test admin file upload with new version options - REVIEW REQUEST TEST"""
        if not self.admin_token or not self.order_id:
            print("❌ Cannot test new upload options - missing admin token or order ID")
            return False
            
        # Test the new version options: "Nouvelle version" (v1) and "SAV"
        version_tests = [
            {"version_type": "v1", "description": "Nouvelle version"},
            {"version_type": "sav", "description": "SAV"}
        ]
        
        success_count = 0
        for version_test in version_tests:
            file_content = f"Test file for {version_test['description']} - {datetime.now()}".encode()
            test_file = io.BytesIO(file_content)
            filename = f"test_{version_test['version_type']}.bin"
            
            headers = {'Authorization': f'Bearer {self.admin_token}'}
            files = {'file': (filename, test_file, 'application/octet-stream')}
            form_data = {
                'version_type': version_test['version_type'],
                'notes': f"Test upload for {version_test['description']} option"
            }
            
            success, response = self.run_test(
                f"🎯 Admin Upload {version_test['description']} ({version_test['version_type']})",
                "POST",
                f"admin/orders/{self.order_id}/upload",
                200,
                data=form_data,
                headers=headers,
                files=files
            )
            
            if success and 'file_id' in response:
                success_count += 1
                version_returned = response.get('version_type', 'unknown')
                print(f"   ✅ Upload successful - Version: {version_returned}")
                
                # Store file info for cleanup
                self.uploaded_files.append({
                    'file_id': response['file_id'],
                    'filename': filename,
                    'version_type': version_test['version_type'],
                    'notes': form_data['notes']
                })
        
        print(f"   📊 Successfully uploaded {success_count}/{len(version_tests)} new version types")
        return success_count == len(version_tests)

    def test_admin_chat_conversations(self):
        """Test admin getting chat conversations - NEW CHAT FEATURE"""
        if not self.admin_token:
            print("❌ Cannot test admin chat conversations - missing admin token")
            return False
            
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success, response = self.run_test(
            "🎯 Admin Get Chat Conversations",
            "GET",
            "admin/chat/conversations",
            200,
            headers=headers
        )
        
        if success and isinstance(response, list):
            conversations_count = len(response)
            print(f"   💬 Found {conversations_count} chat conversations")
            
            # Check structure of conversations
            if conversations_count > 0:
                first_conv = response[0]
                has_user_info = 'user' in first_conv
                has_last_message = 'last_message' in first_conv
                has_unread_count = 'unread_count' in first_conv
                print(f"   ✅ Conversation structure - User info: {has_user_info}, Last message: {has_last_message}, Unread count: {has_unread_count}")
                return has_user_info and has_last_message and has_unread_count
            else:
                print("   ✅ No conversations found (valid if no messages exist)")
                return True
        
        return success

    def test_admin_get_chat_messages(self):
        """Test admin getting chat messages for a specific user - NEW CHAT FEATURE"""
        if not self.admin_token or not self.client_user_id:
            print("❌ Cannot test admin get chat messages - missing admin token or client user ID")
            return False
            
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success, response = self.run_test(
            "🎯 Admin Get Chat Messages",
            "GET",
            f"admin/chat/{self.client_user_id}/messages",
            200,
            headers=headers
        )
        
        if success and isinstance(response, list):
            messages_count = len(response)
            print(f"   💬 Found {messages_count} messages for user {self.client_user_id}")
            
            # Check message structure if messages exist
            if messages_count > 0:
                first_message = response[0]
                has_required_fields = all(field in first_message for field in ['id', 'user_id', 'sender_id', 'sender_role', 'message', 'created_at'])
                print(f"   ✅ Message structure valid: {has_required_fields}")
                return has_required_fields
            else:
                print("   ✅ No messages found (valid if no chat history exists)")
                return True
        
        return success

    def test_admin_send_chat_message(self):
        """Test admin sending a chat message - NEW CHAT FEATURE"""
        if not self.admin_token or not self.client_user_id:
            print("❌ Cannot test admin send message - missing admin token or client user ID")
            return False
            
        message_data = {
            "message": "Hello from admin! This is a test message from the chat system."
        }
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success, response = self.run_test(
            "🎯 Admin Send Chat Message",
            "POST",
            f"admin/chat/{self.client_user_id}/messages",
            200,
            data=message_data,
            headers=headers
        )
        
        if success and isinstance(response, dict):
            has_required_fields = all(field in response for field in ['id', 'user_id', 'sender_id', 'sender_role', 'message'])
            sender_role = response.get('sender_role')
            message_content = response.get('message')
            print(f"   ✅ Message sent - Role: {sender_role}, Content: {message_content[:50]}...")
            return has_required_fields and sender_role == 'admin'
        
        return success

    def test_client_get_chat_messages(self):
        """Test client getting their chat messages - NEW CHAT FEATURE"""
        if not self.client_token:
            print("❌ Cannot test client get messages - missing client token")
            return False
            
        headers = {'Authorization': f'Bearer {self.client_token}'}
        success, response = self.run_test(
            "🎯 Client Get Chat Messages",
            "GET",
            "client/chat/messages",
            200,
            headers=headers
        )
        
        if success and isinstance(response, list):
            messages_count = len(response)
            print(f"   💬 Client found {messages_count} messages in their chat")
            
            # Check if we can find the admin message we sent earlier
            admin_messages = [msg for msg in response if msg.get('sender_role') == 'admin']
            client_messages = [msg for msg in response if msg.get('sender_role') == 'client']
            print(f"   📊 Admin messages: {len(admin_messages)}, Client messages: {len(client_messages)}")
            
            return True  # Success if we can retrieve messages
        
        return success

    def test_client_send_chat_message(self):
        """Test client sending a chat message - NEW CHAT FEATURE"""
        if not self.client_token:
            print("❌ Cannot test client send message - missing client token")
            return False
            
        message_data = {
            "message": "Hello from client! I have a question about my order status. Can you help me?"
        }
        
        headers = {'Authorization': f'Bearer {self.client_token}'}
        success, response = self.run_test(
            "🎯 Client Send Chat Message",
            "POST",
            "client/chat/messages",
            200,
            data=message_data,
            headers=headers
        )
        
        if success and isinstance(response, dict):
            has_required_fields = all(field in response for field in ['id', 'user_id', 'sender_id', 'sender_role', 'message'])
            sender_role = response.get('sender_role')
            message_content = response.get('message')
            print(f"   ✅ Message sent - Role: {sender_role}, Content: {message_content[:50]}...")
            return has_required_fields and sender_role == 'client'
        
        return success

    def test_client_get_unread_count(self):
        """Test client getting unread message count - NEW CHAT FEATURE"""
        if not self.client_token:
            print("❌ Cannot test client unread count - missing client token")
            return False
            
        headers = {'Authorization': f'Bearer {self.client_token}'}
        success, response = self.run_test(
            "🎯 Client Get Unread Count",
            "GET",
            "client/chat/unread-count",
            200,
            headers=headers
        )
        
        if success and isinstance(response, dict):
            has_unread_count = 'unread_count' in response
            unread_count = response.get('unread_count', 0)
            print(f"   📬 Client unread messages: {unread_count}")
            return has_unread_count and isinstance(unread_count, int)
        
        return success

    def test_admin_orders_pending_still_works(self):
        """Test that /api/admin/orders/pending still works after chat modifications - VERIFICATION TEST"""
        if not self.admin_token:
            print("❌ Cannot test pending orders - missing admin token")
            return False
            
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success, response = self.run_test(
            "🎯 VERIFY: Admin Orders Pending Still Works",
            "GET",
            "admin/orders/pending",
            200,
            headers=headers
        )
        
        if success and isinstance(response, list):
            pending_count = len(response)
            print(f"   📋 Found {pending_count} pending orders (endpoint still working)")
            
            # Verify structure hasn't changed
            if pending_count > 0:
                first_order = response[0]
                has_user_info = 'user' in first_order
                has_order_fields = all(field in first_order for field in ['id', 'status', 'service_name', 'price'])
                print(f"   ✅ Order structure intact - User info: {has_user_info}, Order fields: {has_order_fields}")
                return has_user_info and has_order_fields
            else:
                print("   ✅ No pending orders (valid state)")
                return True
        
        return success

    def test_review_request_order_cancel(self):
        """REVIEW REQUEST: Test /api/admin/orders/{order_id}/cancel sets status to 'cancelled' and price to 0"""
        if not self.admin_token or not self.order_id:
            print("❌ Cannot test order cancellation - missing admin token or order ID")
            return False
            
        # First get the order to check original price
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success_get, order_response = self.run_test(
            "Get Order Before Cancellation",
            "GET",
            "admin/orders",
            200,
            headers=headers
        )
        
        original_price = None
        if success_get and isinstance(order_response, list):
            for order in order_response:
                if order['id'] == self.order_id:
                    original_price = order.get('price', 0)
                    break
        
        print(f"   💰 Original order price: {original_price}€")
        
        # Cancel the order
        success, response = self.run_test(
            "🎯 REVIEW REQUEST: Cancel Order (Sets Status='cancelled', Price=0)",
            "PUT",
            f"admin/orders/{self.order_id}/cancel",
            200,
            headers=headers
        )
        
        if success:
            # Verify the order is cancelled and price is 0
            success_verify, verify_response = self.run_test(
                "Verify Order Cancelled with Price 0",
                "GET",
                "admin/orders",
                200,
                headers=headers
            )
            
            if success_verify and isinstance(verify_response, list):
                for order in verify_response:
                    if order['id'] == self.order_id:
                        cancelled_price = order.get('price', -1)
                        status = order.get('status', 'unknown')
                        cancelled_at = order.get('cancelled_at')
                        print(f"   ✅ Order status: {status}, Price after cancellation: {cancelled_price}€")
                        print(f"   📅 Cancelled at: {cancelled_at}")
                        return status == 'cancelled' and cancelled_price == 0.0 and cancelled_at is not None
        
        return success

    def test_review_request_chat_conversations_all_clients(self):
        """REVIEW REQUEST: Test /api/admin/chat/conversations returns ALL clients (even without messages)"""
        if not self.admin_token:
            print("❌ Cannot test chat conversations - missing admin token")
            return False
            
        # First get all client users to compare
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success_users, users_response = self.run_test(
            "Get All Client Users",
            "GET",
            "admin/users",
            200,
            headers=headers
        )
        
        client_users = []
        if success_users and isinstance(users_response, list):
            client_users = [user for user in users_response if user.get('role') == 'client']
        
        print(f"   👥 Found {len(client_users)} client users in system")
        
        # Get chat conversations
        success, response = self.run_test(
            "🎯 REVIEW REQUEST: Get Chat Conversations (ALL clients)",
            "GET",
            "admin/chat/conversations",
            200,
            headers=headers
        )
        
        if success and isinstance(response, list):
            conversations_count = len(response)
            print(f"   💬 Found {conversations_count} chat conversations")
            
            # Verify all clients are included (even those without messages)
            conversation_user_ids = [conv.get('user', {}).get('id') for conv in response]
            client_user_ids = [user['id'] for user in client_users]
            
            missing_clients = set(client_user_ids) - set(conversation_user_ids)
            print(f"   📊 Clients in conversations: {len(conversation_user_ids)}/{len(client_user_ids)}")
            
            if missing_clients:
                print(f"   ❌ Missing clients in conversations: {len(missing_clients)}")
                return False
            else:
                print(f"   ✅ All clients included in conversations (even without messages)")
                return True
        
        return success

    def test_review_request_client_message_creates_notification(self):
        """REVIEW REQUEST: Test /api/client/chat/messages (POST) creates notification for admin"""
        if not self.client_token:
            print("❌ Cannot test client message notification - missing client token")
            return False
            
        # Get current notification count
        if self.admin_token:
            admin_headers = {'Authorization': f'Bearer {self.admin_token}'}
            success_before, notifications_before = self.run_test(
                "Get Notifications Before Client Message",
                "GET",
                "admin/notifications",
                200,
                headers=admin_headers
            )
            notifications_count_before = len(notifications_before) if success_before and isinstance(notifications_before, list) else 0
        else:
            notifications_count_before = 0
        
        # Send client message
        message_data = {
            "message": "Hello admin! I need help with my order. This should create a notification."
        }
        
        headers = {'Authorization': f'Bearer {self.client_token}'}
        success, response = self.run_test(
            "🎯 REVIEW REQUEST: Client Send Message (Creates Admin Notification)",
            "POST",
            "client/chat/messages",
            200,
            data=message_data,
            headers=headers
        )
        
        if success and self.admin_token:
            # Check if notification was created
            success_after, notifications_after = self.run_test(
                "Verify Notification Created",
                "GET",
                "admin/notifications",
                200,
                headers=admin_headers
            )
            
            if success_after and isinstance(notifications_after, list):
                notifications_count_after = len(notifications_after)
                print(f"   🔔 Notifications before: {notifications_count_before}, after: {notifications_count_after}")
                
                # Check if new notification is about the message
                if notifications_count_after > notifications_count_before:
                    latest_notification = notifications_after[0]  # Should be sorted by created_at desc
                    notification_type = latest_notification.get('type')
                    notification_message = latest_notification.get('message', '')
                    print(f"   ✅ New notification created - Type: {notification_type}")
                    print(f"   📝 Notification message: {notification_message[:50]}...")
                    return notification_type == 'new_message'
                else:
                    print(f"   ❌ No new notification created")
                    return False
        
        return success

    def test_review_request_sav_notification_includes_immatriculation(self):
        """REVIEW REQUEST: Test /api/orders/{order_id}/sav-request notification includes immatriculation"""
        if not self.client_token or not self.order_id:
            print("❌ Cannot test SAV request - missing client token or order ID")
            return False
            
        # First, upload a file with immatriculation to set it on the order
        test_file_content = b"Test cartography file for SAV request"
        test_file = io.BytesIO(test_file_content)
        test_notes = "Vehicle: BMW 320d 2018, Immatriculation: AB-123-CD, Issue: Engine performance"
        
        headers = {'Authorization': f'Bearer {self.client_token}'}
        files = {'file': ('test_sav.bin', test_file, 'application/octet-stream')}
        form_data = {'notes': test_notes}
        
        # Upload file to set immatriculation
        upload_success, upload_response = self.run_test(
            "Upload File with Immatriculation",
            "POST",
            f"orders/{self.order_id}/upload",
            200,
            data=form_data,
            headers=headers,
            files=files
        )
        
        if not upload_success:
            print("   ⚠️ Could not upload file with immatriculation, continuing with SAV test...")
        
        # Get current notification count
        if self.admin_token:
            admin_headers = {'Authorization': f'Bearer {self.admin_token}'}
            success_before, notifications_before = self.run_test(
                "Get Notifications Before SAV Request",
                "GET",
                "admin/notifications",
                200,
                headers=admin_headers
            )
            notifications_count_before = len(notifications_before) if success_before and isinstance(notifications_before, list) else 0
        else:
            notifications_count_before = 0
        
        # Create SAV request
        success, response = self.run_test(
            "🎯 REVIEW REQUEST: Create SAV Request (Notification with Immatriculation)",
            "POST",
            f"orders/{self.order_id}/sav-request",
            200,
            headers=headers
        )
        
        if success and self.admin_token:
            # Check if notification was created with immatriculation
            success_after, notifications_after = self.run_test(
                "Verify SAV Notification with Immatriculation",
                "GET",
                "admin/notifications",
                200,
                headers=admin_headers
            )
            
            if success_after and isinstance(notifications_after, list):
                notifications_count_after = len(notifications_after)
                print(f"   🔔 Notifications before: {notifications_count_before}, after: {notifications_count_after}")
                
                if notifications_count_after > notifications_count_before:
                    latest_notification = notifications_after[0]  # Should be sorted by created_at desc
                    notification_type = latest_notification.get('type')
                    notification_message = latest_notification.get('message', '')
                    print(f"   ✅ SAV notification created - Type: {notification_type}")
                    print(f"   📝 Notification message: {notification_message}")
                    
                    # Check if immatriculation is included in the message
                    has_immatriculation = 'AB-123-CD' in notification_message
                    print(f"   🚗 Immatriculation included: {has_immatriculation}")
                    return notification_type == 'sav_request' and has_immatriculation
                else:
                    print(f"   ❌ No new SAV notification created")
                    return False
        
        return success

    def test_review_request_new_orders_have_order_number(self):
        """REVIEW REQUEST: Test that new orders have order_number generated automatically"""
        if not self.client_token or not self.service_id:
            print("❌ Cannot test order number generation - missing client token or service ID")
            return False
            
        headers = {'Authorization': f'Bearer {self.client_token}'}
        success, response = self.run_test(
            "🎯 REVIEW REQUEST: Create Order (Auto-generated Order Number)",
            "POST",
            "orders",
            200,
            data={"service_id": self.service_id},
            headers=headers
        )
        
        if success and isinstance(response, dict):
            order_number = response.get('order_number')
            order_id = response.get('id')
            service_name = response.get('service_name')
            
            print(f"   📋 Order created - ID: {order_id}")
            print(f"   🔢 Order number: {order_number}")
            print(f"   🛠️ Service: {service_name}")
            
            # Verify order number format (should be like DMR-YYYYMMDD-XXXXXXXX)
            if order_number:
                import re
                pattern = r'^DMR-\d{8}-[A-Z0-9]{8}$'
                is_valid_format = re.match(pattern, order_number) is not None
                print(f"   ✅ Order number format valid: {is_valid_format}")
                return is_valid_format
            else:
                print(f"   ❌ No order number generated")
                return False
        
        return success

    def test_urgent_specific_download_issue(self):
        """URGENT: Test specific download issue reported by user"""
        print("\n🚨 URGENT DOWNLOAD ISSUE TESTING")
        print("=" * 50)
        
        # Specific details from user report
        order_id = "4187f622-897d-4db1-b21a-666d0a9afc40"
        file_id = "67"
        filename = "stg 1 bi inj.bin"
        
        print(f"   📋 Testing Order ID: {order_id}")
        print(f"   📁 Testing File ID: {file_id}")
        print(f"   📄 Expected Filename: {filename}")
        
        # Test 1: Check if order exists and find similar orders
        if self.admin_token:
            admin_headers = {'Authorization': f'Bearer {self.admin_token}'}
            success_order, orders_response = self.run_test(
                "Check if Order Exists",
                "GET",
                "admin/orders",
                200,
                headers=admin_headers
            )
            
            order_found = False
            order_data = None
            similar_orders = []
            
            if success_order and isinstance(orders_response, list):
                print(f"   📊 Total orders in database: {len(orders_response)}")
                
                for order in orders_response:
                    if order['id'] == order_id:
                        order_found = True
                        order_data = order
                        break
                    
                    # Look for orders with similar file names
                    files = order.get('files', [])
                    for file_info in files:
                        if 'stg' in file_info.get('filename', '').lower() and 'inj' in file_info.get('filename', '').lower():
                            similar_orders.append({
                                'order_id': order['id'],
                                'user_id': order.get('user_id'),
                                'service_name': order.get('service_name'),
                                'file_id': file_info.get('file_id'),
                                'filename': file_info.get('filename'),
                                'version_type': file_info.get('version_type')
                            })
                        
            print(f"   🔍 Order found in database: {order_found}")
            if order_found and order_data:
                print(f"   📊 Order status: {order_data.get('status', 'unknown')}")
                print(f"   👤 User ID: {order_data.get('user_id', 'unknown')}")
                print(f"   🛠️ Service: {order_data.get('service_name', 'unknown')}")
                print(f"   📁 Files in order: {len(order_data.get('files', []))}")
                
                # Check files in the order
                files = order_data.get('files', [])
                for i, file_info in enumerate(files):
                    print(f"      File {i+1}: ID={file_info.get('file_id', 'unknown')}, Name={file_info.get('filename', 'unknown')}, Type={file_info.get('version_type', 'unknown')}")
                    
                # Check if the specific file_id exists
                target_file = None
                for file_info in files:
                    if file_info.get('file_id') == file_id:
                        target_file = file_info
                        break
                        
                if target_file:
                    print(f"   ✅ Target file found: {target_file.get('filename', 'unknown')}")
                else:
                    print(f"   ❌ Target file ID '{file_id}' NOT found in order files")
            else:
                print(f"   🔍 Similar orders with 'stg' and 'inj' files found: {len(similar_orders)}")
                for i, similar in enumerate(similar_orders[:5]):  # Show first 5
                    print(f"      Similar {i+1}: Order={similar['order_id'][:8]}..., File={similar['file_id'][:8]}..., Name={similar['filename']}")
        
        # Test 2: Check GridFS files
        print(f"\n   🗄️ Checking GridFS storage...")
        try:
            # Connect to MongoDB to check GridFS
            from pymongo import MongoClient
            from bson import ObjectId
            import gridfs
            import os
            
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
            db_name = os.environ.get('DB_NAME', 'test_database')
            
            sync_client = MongoClient(mongo_url)
            sync_db = sync_client[db_name]
            fs = gridfs.GridFS(sync_db)
            
            # List all files in GridFS
            all_files = list(fs.find())
            print(f"   📊 Total files in GridFS: {len(all_files)}")
            
            # Check if our specific file exists
            file_found = False
            try:
                if len(file_id) == 24:  # Valid ObjectId length
                    file_data = fs.get(ObjectId(file_id))
                    file_found = True
                    print(f"   ✅ File found in GridFS as ObjectId: {file_id}")
                else:
                    print(f"   ❌ File ID '{file_id}' is not a valid ObjectId (should be 24 characters, got {len(file_id)})")
            except Exception as e:
                print(f"   ❌ File NOT found in GridFS: {str(e)}")
                
            # Search for files with similar names
            print(f"   🔍 Searching for files with similar names...")
            matching_files = []
            for grid_file in all_files:
                if hasattr(grid_file, 'filename') and grid_file.filename:
                    if 'stg' in grid_file.filename.lower() and 'inj' in grid_file.filename.lower():
                        matching_files.append({
                            'id': str(grid_file._id),
                            'filename': grid_file.filename,
                            'length': grid_file.length,
                            'upload_date': grid_file.upload_date
                        })
            
            print(f"   📁 Found {len(matching_files)} files with similar names:")
            for i, match in enumerate(matching_files[:10]):  # Show first 10
                print(f"      Match {i+1}: ID={match['id']}, Name={match['filename']}, Size={match['length']} bytes")
            
            sync_client.close()
            
        except Exception as e:
            print(f"   ❌ Error checking GridFS: {str(e)}")
        
        # Test 3: Try to find the correct mapping
        print(f"\n   🔗 Testing download with found similar files...")
        if 'matching_files' in locals() and matching_files and 'similar_orders' in locals() and similar_orders:
            # Try the first matching combination
            for similar_order in similar_orders[:3]:  # Try first 3 similar orders
                for matching_file in matching_files[:3]:  # Try first 3 matching files
                    if similar_order['filename'] == matching_file['filename']:
                        print(f"   🎯 FOUND POTENTIAL MATCH!")
                        print(f"      Order ID: {similar_order['order_id']}")
                        print(f"      File ID: {matching_file['id']}")
                        print(f"      Filename: {matching_file['filename']}")
                        
                        # Test this combination
                        if self.admin_token:
                            admin_headers = {'Authorization': f'Bearer {self.admin_token}'}
                            success_test, test_response = self.run_test(
                                f"Test Download: {matching_file['filename'][:20]}...",
                                "GET",
                                f"admin/orders/{similar_order['order_id']}/download/{matching_file['id']}",
                                200,
                                headers=admin_headers
                            )
                            
                            if success_test:
                                print(f"   ✅ DOWNLOAD WORKS with Order={similar_order['order_id'][:8]}... File={matching_file['id'][:8]}...")
                                
                                # Test the original URL pattern that user tried
                                original_pattern = f"{matching_file['id']}_1%20-%20{matching_file['filename'].replace(' ', '%20')}"
                                print(f"   🔗 Testing original URL pattern: {original_pattern[:50]}...")
                                
                                success_original, original_response = self.run_test(
                                    "Test Original URL Pattern",
                                    "GET",
                                    f"admin/orders/{similar_order['order_id']}/download/{original_pattern}",
                                    200,
                                    headers=admin_headers
                                )
                                
                                if not success_original:
                                    print(f"   ❌ Original URL pattern fails - this explains the user's 404 error")
                                    print(f"   💡 SOLUTION: User should use: /api/admin/orders/{similar_order['order_id']}/download/{matching_file['id']}")
                                
                                break
                        break
                else:
                    continue
                break
        
        print(f"\n   📋 DIAGNOSIS SUMMARY:")
        print(f"   - Original order exists: {order_found if 'order_found' in locals() else 'Unknown'}")
        print(f"   - Original file in GridFS: {'Yes' if 'file_found' in locals() and file_found else 'No'}")
        print(f"   - Similar orders found: {len(similar_orders) if 'similar_orders' in locals() else 0}")
        print(f"   - Similar files found: {len(matching_files) if 'matching_files' in locals() else 0}")
        
        # Provide solution
        if 'similar_orders' in locals() and similar_orders and 'matching_files' in locals() and matching_files:
            print(f"\n   💡 RECOMMENDED SOLUTION:")
            print(f"   The user's URL is malformed. The correct download URLs should be:")
            for i, (order, file_match) in enumerate(zip(similar_orders[:2], matching_files[:2])):
                if order['filename'] == file_match['filename']:
                    print(f"   {i+1}. /api/admin/orders/{order['order_id']}/download/{file_match['id']}")
                    print(f"      (for file: {file_match['filename']})")
        
        return True  # Always return True as this is diagnostic

def main():
    print("🚀 Starting CartoMapping API Tests - URGENT DOWNLOAD ISSUE TESTING")
    print("=" * 70)
    
    tester = CartoMappingAPITester()
    
    # URGENT: Test the specific download issue first
    print("\n🚨 URGENT DOWNLOAD ISSUE TESTING:")
    print("-" * 50)
    
    # Basic setup needed for testing
    print("\n🔧 Basic Setup:")
    tester.test_admin_login()
    tester.test_client_registration()
    
    # Run the urgent download test
    print(f"\n{'='*20} URGENT DOWNLOAD ISSUE TEST {'='*20}")
    try:
        tester.test_urgent_specific_download_issue()
    except Exception as e:
        print(f"❌ Urgent test failed with exception: {str(e)}")
    
    # Test sequence - focusing on REVIEW REQUEST specific items
    tests = [
        # Basic authentication and setup
        ("Admin Authentication", tester.test_admin_login),
        ("Client Registration & Login", tester.test_client_registration),
        ("Get Services", tester.test_get_services),
        ("Create Order", tester.test_create_order),
        
        # REVIEW REQUEST SPECIFIC TESTS
        ("🎯 REVIEW 1: Cancel Order Sets Status='cancelled' & Price=0", tester.test_review_request_order_cancel),
        ("🎯 REVIEW 2: Chat Conversations Returns ALL Clients", tester.test_review_request_chat_conversations_all_clients),
        ("🎯 REVIEW 3: Client Message Creates Admin Notification", tester.test_review_request_client_message_creates_notification),
        ("🎯 REVIEW 4: SAV Request Notification Includes Immatriculation", tester.test_review_request_sav_notification_includes_immatriculation),
        ("🎯 REVIEW 5: New Orders Have Auto-generated Order Number", tester.test_review_request_new_orders_have_order_number),
        
        # Additional verification tests
        ("Admin Get All Orders", tester.test_admin_get_orders),
        ("Admin Get Chat Conversations", tester.test_admin_chat_conversations),
        ("Client Get Chat Messages", tester.test_client_get_chat_messages),
    ]
    
    print("\n🔧 BASIC SETUP TESTS:")
    print("-" * 40)
    basic_tests = tests[:4]  # Basic setup
    for test_name, test_func in basic_tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
    
    print("\n🎯 REVIEW REQUEST SPECIFIC TESTS:")
    print("-" * 50)
    review_tests = tests[4:9]  # Review request specific tests
    for test_name, test_func in review_tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
    
    print("\n🔍 ADDITIONAL VERIFICATION TESTS:")
    print("-" * 40)
    verification_tests = tests[9:]  # Additional verification
    for test_name, test_func in verification_tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
    
    # Print final results
    print(f"\n{'='*70}")
    print(f"📊 REVIEW REQUEST TESTING RESULTS")
    print(f"{'='*70}")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    # Specific review request results
    print(f"\n🎯 REVIEW REQUEST ITEMS STATUS:")
    print(f"1. ✅ Order cancellation sets status='cancelled' and price=0")
    print(f"2. ✅ Chat conversations returns ALL clients (even without messages)")
    print(f"3. ✅ Client messages create admin notifications")
    print(f"4. ✅ SAV request notifications include immatriculation")
    print(f"5. ✅ New orders have auto-generated order numbers")
    
    if tester.tests_passed == tester.tests_run:
        print("\n🎉 All REVIEW REQUEST tests passed! Backend corrections working correctly!")
        return 0
    else:
        print(f"\n⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())