#!/usr/bin/env python3

import requests
import sys
import json
import io
from datetime import datetime

class ReviewRequestTester:
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
        self.uploaded_files = []

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
                    # Form data
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

    def setup_authentication(self):
        """Setup admin and client authentication"""
        print("\n🔐 Setting up authentication...")
        
        # Admin login
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@test.com", "password": "admin123"}
        )
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            print("✅ Admin authenticated")
        else:
            print("❌ Admin authentication failed")
            return False

        # Create/login client
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
            # Login with the new client
            login_success, login_response = self.run_test(
                "Client Login",
                "POST",
                "auth/login",
                200,
                data={"email": client_data["email"], "password": client_data["password"]}
            )
            if login_success and 'access_token' in login_response:
                self.client_token = login_response['access_token']
                print("✅ Client authenticated")
            else:
                print("❌ Client login failed")
                return False
        else:
            print("❌ Client registration failed")
            return False

        # Get services and create an order for testing
        success, response = self.run_test(
            "Get Services",
            "GET",
            "services",
            200
        )
        if success and len(response) > 0:
            self.service_id = response[0]['id']
            
            # Create order
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
                print("✅ Test order created")
            else:
                print("❌ Order creation failed")
                return False
        else:
            print("❌ Services retrieval failed")
            return False

        return True

    def test_client_notifications_endpoint(self):
        """Test 1: /api/client/notifications endpoint"""
        if not self.client_token:
            print("❌ Cannot test client notifications - missing client token")
            return False

        headers = {'Authorization': f'Bearer {self.client_token}'}
        success, response = self.run_test(
            "🎯 REVIEW 1: Client Get Notifications",
            "GET",
            "client/notifications",
            200,
            headers=headers
        )
        
        if success and isinstance(response, list):
            print(f"   📬 Found {len(response)} notifications for client")
            # Check notification structure if any exist
            if len(response) > 0:
                first_notif = response[0]
                has_required_fields = all(field in first_notif for field in ['id', 'type', 'title', 'message', 'is_read', 'created_at'])
                print(f"   ✅ Notification structure valid: {has_required_fields}")
                return has_required_fields
            else:
                print("   ✅ No notifications found (valid state)")
                return True
        
        return success

    def test_admin_upload_creates_client_notification(self):
        """Test 2: /api/admin/orders/{order_id}/upload creates client notifications"""
        if not self.admin_token or not self.order_id:
            print("❌ Cannot test admin upload - missing admin token or order ID")
            return False

        # Get current client notification count
        client_headers = {'Authorization': f'Bearer {self.client_token}'}
        success_before, notifications_before = self.run_test(
            "Get Client Notifications Before Upload",
            "GET",
            "client/notifications",
            200,
            headers=client_headers
        )
        notifications_count_before = len(notifications_before) if success_before and isinstance(notifications_before, list) else 0

        # Admin uploads a file
        test_file_content = b"This is a test modified cartography file - Stage 1 tuning applied"
        test_file = io.BytesIO(test_file_content)
        admin_notes = "Applied Stage 1 tuning, file ready for download"
        version_type = "v1"
        
        admin_headers = {'Authorization': f'Bearer {self.admin_token}'}
        files = {'file': ('modified_cartography_v1.bin', test_file, 'application/octet-stream')}
        form_data = {
            'version_type': version_type,
            'notes': admin_notes
        }
        
        success, response = self.run_test(
            "🎯 REVIEW 2: Admin Upload File (Should Create Client Notification)",
            "POST",
            f"admin/orders/{self.order_id}/upload",
            200,
            data=form_data,
            headers=admin_headers,
            files=files
        )
        
        if success and 'file_id' in response:
            self.uploaded_files.append({
                'file_id': response['file_id'],
                'filename': 'modified_cartography_v1.bin',
                'version_type': version_type,
                'notes': admin_notes
            })
            
            # Check if client notification was created
            success_after, notifications_after = self.run_test(
                "Verify Client Notification Created",
                "GET",
                "client/notifications",
                200,
                headers=client_headers
            )
            
            if success_after and isinstance(notifications_after, list):
                notifications_count_after = len(notifications_after)
                print(f"   🔔 Client notifications before: {notifications_count_before}, after: {notifications_count_after}")
                
                if notifications_count_after > notifications_count_before:
                    latest_notification = notifications_after[0]  # Should be sorted by created_at desc
                    notification_type = latest_notification.get('type')
                    notification_message = latest_notification.get('message', '')
                    print(f"   ✅ New client notification created - Type: {notification_type}")
                    print(f"   📝 Notification message: {notification_message}")
                    return notification_type == 'new_file'
                else:
                    print(f"   ❌ No new client notification created")
                    return False
        
        return success

    def test_client_mark_notification_read(self):
        """Test 3: /api/client/notifications/{notification_id}/read endpoint"""
        if not self.client_token:
            print("❌ Cannot test mark notification read - missing client token")
            return False

        # Get client notifications to find one to mark as read
        headers = {'Authorization': f'Bearer {self.client_token}'}
        success_get, notifications = self.run_test(
            "Get Client Notifications",
            "GET",
            "client/notifications",
            200,
            headers=headers
        )
        
        if success_get and isinstance(notifications, list) and len(notifications) > 0:
            # Find an unread notification
            unread_notification = None
            for notif in notifications:
                if not notif.get('is_read', True):
                    unread_notification = notif
                    break
            
            if not unread_notification:
                # If no unread notifications, use the first one
                unread_notification = notifications[0]
            
            notification_id = unread_notification['id']
            print(f"   🔔 Testing with notification: {notification_id}")
            
            # Mark notification as read
            success, response = self.run_test(
                "🎯 REVIEW 3: Mark Client Notification as Read",
                "PUT",
                f"client/notifications/{notification_id}/read",
                200,
                headers=headers
            )
            
            if success:
                # Verify notification is marked as read
                success_verify, verify_notifications = self.run_test(
                    "Verify Notification Marked as Read",
                    "GET",
                    "client/notifications",
                    200,
                    headers=headers
                )
                
                if success_verify and isinstance(verify_notifications, list):
                    for notif in verify_notifications:
                        if notif['id'] == notification_id:
                            is_read = notif.get('is_read', False)
                            print(f"   ✅ Notification read status: {is_read}")
                            return is_read
            
            return success
        else:
            print("   ⚠️ No notifications found to test read functionality")
            return True  # Not a failure if no notifications exist

    def test_file_download_endpoints(self):
        """Test 4: /api/orders/{order_id}/files/{file_id}/download endpoints"""
        if not self.client_token or not self.order_id or not self.uploaded_files:
            print("❌ Cannot test file download - missing client token, order ID, or uploaded files")
            return False

        file_info = self.uploaded_files[0]  # Use first uploaded file
        headers = {'Authorization': f'Bearer {self.client_token}'}
        
        # Test client download
        success, response = self.run_test(
            "🎯 REVIEW 4: Client Download File",
            "GET",
            f"orders/{self.order_id}/download/{file_info['file_id']}",
            200,
            headers=headers
        )
        
        if success:
            print(f"   ✅ Client file download successful")
            
            # Test admin download as well
            if self.admin_token:
                admin_headers = {'Authorization': f'Bearer {self.admin_token}'}
                admin_success, admin_response = self.run_test(
                    "Admin Download File",
                    "GET",
                    f"admin/orders/{self.order_id}/download/{file_info['file_id']}",
                    200,
                    headers=admin_headers
                )
                
                if admin_success:
                    print(f"   ✅ Admin file download successful")
                    return True
                else:
                    print(f"   ⚠️ Admin download failed, but client download works")
                    return True  # Client download working is the main requirement
        
        return success

    def run_all_tests(self):
        """Run all review request tests"""
        print("🚀 Starting Review Request Focused Testing")
        print("=" * 60)
        
        # Setup
        if not self.setup_authentication():
            print("❌ Authentication setup failed, cannot continue")
            return False

        # Run the specific review request tests
        tests = [
            ("Test 1: Client Notifications Endpoint", self.test_client_notifications_endpoint),
            ("Test 2: Admin Upload Creates Client Notification", self.test_admin_upload_creates_client_notification),
            ("Test 3: Client Mark Notification Read", self.test_client_mark_notification_read),
            ("Test 4: File Download Endpoints", self.test_file_download_endpoints),
        ]
        
        print(f"\n🎯 REVIEW REQUEST TESTS:")
        print("-" * 40)
        
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                test_func()
            except Exception as e:
                print(f"❌ Test failed with exception: {str(e)}")

        # Print final results
        print(f"\n{'='*60}")
        print(f"📊 REVIEW REQUEST TESTING RESULTS")
        print(f"{'='*60}")
        print(f"Tests passed: {self.tests_passed}/{self.tests_run}")
        print(f"Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All review request tests passed!")
            return True
        else:
            print(f"\n⚠️ {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    tester = ReviewRequestTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ All review request functionality is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Some review request functionality needs attention")
        sys.exit(1)

if __name__ == "__main__":
    main()