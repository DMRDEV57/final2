#!/usr/bin/env python3

import requests
import sys
import json
import io
from datetime import datetime

class UrgentCancelNotificationTester:
    def __init__(self, base_url="https://ba7542fd-fff4-49dc-8761-c0598ae50777.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.client_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.client_user_id = None
        self.service_id = None
        self.test_order_id = None
        self.notification_ids = []

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
                    print(f"   Response: {json.dumps(response_data, indent=2)[:300]}...")
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
            print(f"   ✅ Admin token obtained")
            return True
        return False

    def test_client_registration_and_login(self):
        """Test client registration and login"""
        timestamp = datetime.now().strftime('%H%M%S')
        client_data = {
            "email": f"urgent_test_client_{timestamp}@example.com",
            "password": "TestPass123!",
            "first_name": "Urgent",
            "last_name": "TestClient",
            "phone": "0123456789",
            "company": "Urgent Test Company"
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
                print(f"   ✅ Client token obtained")
                return True
        return False

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
            print(f"   ✅ Found {len(response)} services, using service ID: {self.service_id}")
            return True
        return False

    def test_create_test_order(self):
        """Create a test order for cancellation testing"""
        if not self.client_token or not self.service_id:
            print("❌ Cannot create test order - missing client token or service ID")
            return False
            
        headers = {'Authorization': f'Bearer {self.client_token}'}
        success, response = self.run_test(
            "Create Test Order for Cancellation",
            "POST",
            "orders",
            200,
            data={"service_id": self.service_id},
            headers=headers
        )
        if success and 'id' in response:
            self.test_order_id = response['id']
            original_price = response.get('price', 0)
            print(f"   ✅ Test order created - ID: {self.test_order_id}, Price: {original_price}€")
            return True
        return False

    def test_cancel_order_endpoint(self):
        """🎯 URGENT TEST: Test PUT /api/admin/orders/{order_id}/cancel"""
        if not self.admin_token or not self.test_order_id:
            print("❌ Cannot test order cancellation - missing admin token or test order ID")
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
        original_status = None
        if success_get and isinstance(order_response, list):
            for order in order_response:
                if order['id'] == self.test_order_id:
                    original_price = order.get('price', 0)
                    original_status = order.get('status', 'unknown')
                    break
        
        print(f"   💰 BEFORE CANCEL - Status: {original_status}, Price: {original_price}€")
        
        # Cancel the order using the cancel endpoint
        success, response = self.run_test(
            "🎯 URGENT: PUT /api/admin/orders/{order_id}/cancel",
            "PUT",
            f"admin/orders/{self.test_order_id}/cancel",
            200,
            headers=headers
        )
        
        if success:
            # Verify the order is cancelled and price is 0
            success_verify, verify_response = self.run_test(
                "Verify Order After Cancellation",
                "GET",
                "admin/orders",
                200,
                headers=headers
            )
            
            if success_verify and isinstance(verify_response, list):
                for order in verify_response:
                    if order['id'] == self.test_order_id:
                        cancelled_price = order.get('price', -1)
                        status = order.get('status', 'unknown')
                        cancelled_at = order.get('cancelled_at')
                        
                        print(f"   📊 AFTER CANCEL - Status: {status}, Price: {cancelled_price}€")
                        print(f"   📅 Cancelled at: {cancelled_at}")
                        
                        # Check if cancellation worked correctly
                        status_correct = status == 'cancelled'
                        price_correct = cancelled_price == 0.0
                        timestamp_exists = cancelled_at is not None
                        
                        print(f"   ✅ Status changed to 'cancelled': {status_correct}")
                        print(f"   ✅ Price set to 0.0: {price_correct}")
                        print(f"   ✅ Cancelled timestamp added: {timestamp_exists}")
                        
                        return status_correct and price_correct and timestamp_exists
        
        return success

    def test_cancel_order_via_status_endpoint(self):
        """🎯 URGENT TEST: Test PUT /api/admin/orders/{order_id}/status with status='cancelled'"""
        if not self.admin_token:
            print("❌ Cannot test status endpoint cancellation - missing admin token")
            return False
            
        # Create another test order for this test
        if not self.client_token or not self.service_id:
            print("❌ Cannot create second test order - missing client token or service ID")
            return False
            
        headers_client = {'Authorization': f'Bearer {self.client_token}'}
        success_create, create_response = self.run_test(
            "Create Second Test Order",
            "POST",
            "orders",
            200,
            data={"service_id": self.service_id},
            headers=headers_client
        )
        
        if not success_create or 'id' not in create_response:
            print("❌ Could not create second test order")
            return False
            
        second_order_id = create_response['id']
        original_price = create_response.get('price', 0)
        print(f"   💰 Second order created - ID: {second_order_id}, Price: {original_price}€")
        
        # Cancel using status endpoint
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success, response = self.run_test(
            "🎯 URGENT: PUT /api/admin/orders/{order_id}/status with 'cancelled'",
            "PUT",
            f"admin/orders/{second_order_id}/status",
            200,
            data={"status": "cancelled"},
            headers=headers
        )
        
        if success:
            # Verify the order status changed but check if price was set to 0
            success_verify, verify_response = self.run_test(
                "Verify Order After Status Cancellation",
                "GET",
                "admin/orders",
                200,
                headers=headers
            )
            
            if success_verify and isinstance(verify_response, list):
                for order in verify_response:
                    if order['id'] == second_order_id:
                        cancelled_price = order.get('price', -1)
                        status = order.get('status', 'unknown')
                        
                        print(f"   📊 AFTER STATUS CANCEL - Status: {status}, Price: {cancelled_price}€")
                        
                        status_correct = status == 'cancelled'
                        price_behavior = cancelled_price  # Check what happens to price
                        
                        print(f"   ✅ Status changed to 'cancelled': {status_correct}")
                        print(f"   📝 Price after status cancel: {price_behavior}€ (should this be 0?)")
                        
                        # This test shows the difference between the two endpoints
                        return status_correct
        
        return success

    def test_create_notifications_for_deletion(self):
        """Create some notifications for deletion testing"""
        if not self.client_token or not self.test_order_id:
            print("❌ Cannot create notifications - missing client token or order ID")
            return False
            
        headers = {'Authorization': f'Bearer {self.client_token}'}
        
        # Create multiple SAV requests to generate notifications
        notifications_created = 0
        for i in range(3):
            success, response = self.run_test(
                f"Create SAV Request {i+1} (for notification)",
                "POST",
                f"orders/{self.test_order_id}/sav-request",
                200,
                headers=headers
            )
            if success:
                notifications_created += 1
        
        print(f"   ✅ Created {notifications_created} notifications via SAV requests")
        return notifications_created > 0

    def test_get_notifications_before_deletion(self):
        """Get current notifications to prepare for deletion tests"""
        if not self.admin_token:
            print("❌ Cannot get notifications - missing admin token")
            return False
            
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success, response = self.run_test(
            "Get Admin Notifications Before Deletion",
            "GET",
            "admin/notifications",
            200,
            headers=headers
        )
        
        if success and isinstance(response, list):
            self.notification_ids = [notif['id'] for notif in response]
            print(f"   📋 Found {len(self.notification_ids)} notifications available for deletion")
            
            # Show some details about notifications
            for i, notif in enumerate(response[:3]):  # Show first 3
                notif_type = notif.get('type', 'unknown')
                notif_title = notif.get('title', 'No title')
                print(f"   🔔 Notification {i+1}: {notif_type} - {notif_title}")
            
            return len(self.notification_ids) > 0
        
        return success

    def test_delete_single_notification(self):
        """🎯 URGENT TEST: Test DELETE /api/admin/notifications/{id}"""
        if not self.admin_token or not self.notification_ids:
            print("❌ Cannot test single notification deletion - missing admin token or notification IDs")
            return False
            
        # Pick the first notification to delete
        notification_to_delete = self.notification_ids[0]
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        print(f"   🎯 Attempting to delete notification: {notification_to_delete}")
        
        success, response = self.run_test(
            "🎯 URGENT: DELETE /api/admin/notifications/{id}",
            "DELETE",
            f"admin/notifications/{notification_to_delete}",
            200,
            headers=headers
        )
        
        if success:
            # Verify the notification was deleted
            success_verify, verify_response = self.run_test(
                "Verify Single Notification Deleted",
                "GET",
                "admin/notifications",
                200,
                headers=headers
            )
            
            if success_verify and isinstance(verify_response, list):
                remaining_ids = [notif['id'] for notif in verify_response]
                was_deleted = notification_to_delete not in remaining_ids
                
                print(f"   ✅ Notification deleted successfully: {was_deleted}")
                print(f"   📊 Notifications before: {len(self.notification_ids)}, after: {len(remaining_ids)}")
                
                # Update our list for next test
                self.notification_ids = remaining_ids
                return was_deleted
        
        return success

    def test_delete_all_notifications(self):
        """🎯 URGENT TEST: Test DELETE /api/admin/notifications"""
        if not self.admin_token:
            print("❌ Cannot test delete all notifications - missing admin token")
            return False
            
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Get count before deletion
        notifications_before = len(self.notification_ids)
        print(f"   📊 Notifications to delete: {notifications_before}")
        
        success, response = self.run_test(
            "🎯 URGENT: DELETE /api/admin/notifications (all)",
            "DELETE",
            "admin/notifications",
            200,
            headers=headers
        )
        
        if success:
            # Verify all notifications were deleted
            success_verify, verify_response = self.run_test(
                "Verify All Notifications Deleted",
                "GET",
                "admin/notifications",
                200,
                headers=headers
            )
            
            if success_verify and isinstance(verify_response, list):
                notifications_after = len(verify_response)
                all_deleted = notifications_after == 0
                
                print(f"   ✅ All notifications deleted: {all_deleted}")
                print(f"   📊 Notifications before: {notifications_before}, after: {notifications_after}")
                
                if 'deleted_count' in response or 'message' in response:
                    print(f"   📝 Server response: {response}")
                
                return all_deleted
        
        return success

def main():
    print("🚨 URGENT TESTING: Cancel Order Status & Notification Deletion Issues")
    print("=" * 80)
    print("Testing specific issues reported by user:")
    print("1. Le statut 'Annulé' ne fonctionne toujours pas")
    print("2. La suppression des notifications ne fonctionne plus")
    print("=" * 80)
    
    tester = UrgentCancelNotificationTester()
    
    # Test sequence focusing on the urgent issues
    tests = [
        # Setup
        ("Setup: Admin Login", tester.test_admin_login),
        ("Setup: Client Registration & Login", tester.test_client_registration_and_login),
        ("Setup: Get Services", tester.test_get_services),
        ("Setup: Create Test Order", tester.test_create_test_order),
        
        # URGENT ISSUE 1: Cancel Order Status
        ("🎯 URGENT 1a: Test Cancel Order Endpoint", tester.test_cancel_order_endpoint),
        ("🎯 URGENT 1b: Test Cancel via Status Endpoint", tester.test_cancel_order_via_status_endpoint),
        
        # URGENT ISSUE 2: Notification Deletion
        ("Setup: Create Notifications", tester.test_create_notifications_for_deletion),
        ("Setup: Get Notifications", tester.test_get_notifications_before_deletion),
        ("🎯 URGENT 2a: Test Delete Single Notification", tester.test_delete_single_notification),
        ("🎯 URGENT 2b: Test Delete All Notifications", tester.test_delete_all_notifications),
    ]
    
    print("\n🔧 RUNNING URGENT TESTS:")
    print("-" * 50)
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🔍 {test_name}")
        print(f"{'='*60}")
        try:
            result = test_func()
            if result:
                print(f"✅ {test_name} - PASSED")
            else:
                print(f"❌ {test_name} - FAILED")
        except Exception as e:
            print(f"💥 {test_name} - EXCEPTION: {str(e)}")
    
    # Print final results
    print(f"\n{'='*80}")
    print(f"📊 URGENT TESTING RESULTS")
    print(f"{'='*80}")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    print(f"\n🎯 URGENT ISSUES STATUS:")
    print(f"1. Cancel Order Status:")
    print(f"   - PUT /api/admin/orders/{{id}}/cancel endpoint")
    print(f"   - PUT /api/admin/orders/{{id}}/status with 'cancelled'")
    print(f"2. Notification Deletion:")
    print(f"   - DELETE /api/admin/notifications/{{id}} (single)")
    print(f"   - DELETE /api/admin/notifications (all)")
    
    if tester.tests_passed == tester.tests_run:
        print("\n🎉 All urgent tests passed! Issues may be resolved.")
    else:
        print(f"\n⚠️ {tester.tests_run - tester.tests_passed} tests failed. Issues need investigation.")
    
    return tester.tests_passed == tester.tests_run

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)