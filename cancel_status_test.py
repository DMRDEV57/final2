#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class CancelStatusTester:
    def __init__(self, base_url="https://ba7542fd-fff4-49dc-8761-c0598ae50777.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.client_token = None
        self.client_user_id = None
        self.service_id = None
        self.test_order_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if headers:
            test_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            if success:
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
            print("✅ Admin authenticated successfully")
        else:
            print("❌ Admin authentication failed")
            return False

        # Create and login client
        timestamp = datetime.now().strftime('%H%M%S')
        client_data = {
            "email": f"cancel_test_client_{timestamp}@example.com",
            "password": "TestPass123!",
            "first_name": "Cancel",
            "last_name": "TestClient",
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
                print("✅ Client authenticated successfully")
                return True
        
        print("❌ Client authentication failed")
        return False

    def get_service_id(self):
        """Get a service ID for testing"""
        success, response = self.run_test(
            "Get Services",
            "GET",
            "services",
            200
        )
        if success and len(response) > 0:
            self.service_id = response[0]['id']
            print(f"✅ Got service ID: {self.service_id}")
            return True
        return False

    def create_test_order(self):
        """Create a test order for cancellation testing"""
        if not self.client_token or not self.service_id:
            print("❌ Cannot create test order - missing client token or service ID")
            return False
            
        headers = {'Authorization': f'Bearer {self.client_token}'}
        success, response = self.run_test(
            "Create Test Order",
            "POST",
            "orders",
            200,
            data={"service_id": self.service_id},
            headers=headers
        )
        if success and 'id' in response:
            self.test_order_id = response['id']
            original_price = response.get('price', 0)
            print(f"✅ Test order created - ID: {self.test_order_id}, Price: {original_price}€")
            return True
        return False

    def test_cancel_endpoint(self):
        """Test /api/admin/orders/{order_id}/cancel endpoint"""
        if not self.admin_token or not self.test_order_id:
            print("❌ Cannot test cancel endpoint - missing admin token or order ID")
            return False

        print(f"\n🎯 TESTING CANCEL ENDPOINT: /api/admin/orders/{self.test_order_id}/cancel")
        
        # Get order before cancellation
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success_get, orders = self.run_test(
            "Get Order Before Cancellation",
            "GET",
            "admin/orders",
            200,
            headers=headers
        )
        
        original_price = None
        original_status = None
        if success_get and isinstance(orders, list):
            for order in orders:
                if order['id'] == self.test_order_id:
                    original_price = order.get('price', 0)
                    original_status = order.get('status', 'unknown')
                    break
        
        print(f"   📊 BEFORE CANCELLATION:")
        print(f"      Status: {original_status}")
        print(f"      Price: {original_price}€")
        
        # Cancel the order
        success, response = self.run_test(
            "Cancel Order via /cancel endpoint",
            "PUT",
            f"admin/orders/{self.test_order_id}/cancel",
            200,
            headers=headers
        )
        
        if success:
            # Verify cancellation
            success_verify, verify_orders = self.run_test(
                "Verify Order After Cancellation",
                "GET",
                "admin/orders",
                200,
                headers=headers
            )
            
            if success_verify and isinstance(verify_orders, list):
                for order in verify_orders:
                    if order['id'] == self.test_order_id:
                        new_price = order.get('price', -1)
                        new_status = order.get('status', 'unknown')
                        cancelled_at = order.get('cancelled_at')
                        
                        print(f"   📊 AFTER CANCELLATION:")
                        print(f"      Status: {new_status}")
                        print(f"      Price: {new_price}€")
                        print(f"      Cancelled at: {cancelled_at}")
                        
                        # Check if cancellation worked correctly
                        status_correct = new_status == 'cancelled'
                        price_correct = new_price == 0.0
                        timestamp_added = cancelled_at is not None
                        
                        print(f"   ✅ RESULTS:")
                        print(f"      Status set to 'cancelled': {status_correct}")
                        print(f"      Price set to 0.0: {price_correct}")
                        print(f"      Cancelled timestamp added: {timestamp_added}")
                        
                        return status_correct and price_correct and timestamp_added
        
        return False

    def test_status_endpoint_with_cancelled(self):
        """Test /api/admin/orders/{order_id}/status endpoint with 'cancelled' status"""
        if not self.admin_token:
            print("❌ Cannot test status endpoint - missing admin token")
            return False

        # Create another test order for this test
        if not self.create_test_order():
            print("❌ Could not create second test order")
            return False

        print(f"\n🎯 TESTING STATUS ENDPOINT: /api/admin/orders/{self.test_order_id}/status")
        
        # Get order before status change
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success_get, orders = self.run_test(
            "Get Order Before Status Change",
            "GET",
            "admin/orders",
            200,
            headers=headers
        )
        
        original_price = None
        original_status = None
        if success_get and isinstance(orders, list):
            for order in orders:
                if order['id'] == self.test_order_id:
                    original_price = order.get('price', 0)
                    original_status = order.get('status', 'unknown')
                    break
        
        print(f"   📊 BEFORE STATUS CHANGE:")
        print(f"      Status: {original_status}")
        print(f"      Price: {original_price}€")
        
        # Change status to cancelled
        success, response = self.run_test(
            "Change Status to 'cancelled'",
            "PUT",
            f"admin/orders/{self.test_order_id}/status",
            200,
            data={"status": "cancelled", "admin_notes": "Test cancellation via status endpoint"},
            headers=headers
        )
        
        if success:
            # Verify status change
            success_verify, verify_orders = self.run_test(
                "Verify Order After Status Change",
                "GET",
                "admin/orders",
                200,
                headers=headers
            )
            
            if success_verify and isinstance(verify_orders, list):
                for order in verify_orders:
                    if order['id'] == self.test_order_id:
                        new_price = order.get('price', -1)
                        new_status = order.get('status', 'unknown')
                        completed_at = order.get('completed_at')
                        admin_notes = order.get('admin_notes', '')
                        
                        print(f"   📊 AFTER STATUS CHANGE:")
                        print(f"      Status: {new_status}")
                        print(f"      Price: {new_price}€")
                        print(f"      Completed at: {completed_at}")
                        print(f"      Admin notes: {admin_notes}")
                        
                        # Check if status change worked
                        status_correct = new_status == 'cancelled'
                        notes_added = 'Test cancellation' in admin_notes
                        
                        print(f"   ✅ RESULTS:")
                        print(f"      Status set to 'cancelled': {status_correct}")
                        print(f"      Admin notes added: {notes_added}")
                        print(f"      Price unchanged: {new_price}€ (Note: status endpoint doesn't modify price)")
                        
                        return status_correct and notes_added
        
        return False

    def test_cancelled_orders_in_database(self):
        """Test that cancelled orders appear correctly in database queries"""
        if not self.admin_token:
            print("❌ Cannot test database queries - missing admin token")
            return False

        print(f"\n🎯 TESTING DATABASE QUERIES FOR CANCELLED ORDERS")
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Get all orders
        success, all_orders = self.run_test(
            "Get All Orders",
            "GET",
            "admin/orders",
            200,
            headers=headers
        )
        
        if success and isinstance(all_orders, list):
            cancelled_orders = [order for order in all_orders if order.get('status') == 'cancelled']
            print(f"   📊 Found {len(cancelled_orders)} cancelled orders in database")
            
            for i, order in enumerate(cancelled_orders[:3]):  # Show first 3
                order_id = order.get('id', 'unknown')[:8]
                price = order.get('price', 'unknown')
                cancelled_at = order.get('cancelled_at', 'unknown')
                service_name = order.get('service_name', 'unknown')
                
                print(f"   📋 Cancelled Order {i+1}:")
                print(f"      ID: {order_id}...")
                print(f"      Service: {service_name}")
                print(f"      Price: {price}€")
                print(f"      Cancelled at: {cancelled_at}")
            
            # Test pending orders endpoint (should exclude cancelled)
            success_pending, pending_orders = self.run_test(
                "Get Pending Orders (Should Exclude Cancelled)",
                "GET",
                "admin/orders/pending",
                200,
                headers=headers
            )
            
            if success_pending and isinstance(pending_orders, list):
                cancelled_in_pending = [order for order in pending_orders if order.get('status') == 'cancelled']
                print(f"   📊 Cancelled orders in pending list: {len(cancelled_in_pending)} (should be 0)")
                
                return len(cancelled_orders) > 0 and len(cancelled_in_pending) == 0
        
        return False

def main():
    print("🚀 URGENT INVESTIGATION: Testing 'Annulé' (Cancelled) Status Functionality")
    print("=" * 80)
    print("🎯 FOCUS: Testing both /cancel and /status endpoints for order cancellation")
    print("=" * 80)
    
    tester = CancelStatusTester()
    
    # Setup phase
    print("\n📋 PHASE 1: SETUP")
    print("-" * 40)
    
    if not tester.setup_authentication():
        print("❌ Authentication setup failed - cannot continue")
        return
    
    if not tester.get_service_id():
        print("❌ Could not get service ID - cannot continue")
        return
    
    if not tester.create_test_order():
        print("❌ Could not create test order - cannot continue")
        return
    
    # Testing phase
    print("\n📋 PHASE 2: CANCEL ENDPOINT TESTING")
    print("-" * 40)
    cancel_endpoint_works = tester.test_cancel_endpoint()
    
    print("\n📋 PHASE 3: STATUS ENDPOINT TESTING")
    print("-" * 40)
    status_endpoint_works = tester.test_status_endpoint_with_cancelled()
    
    print("\n📋 PHASE 4: DATABASE VERIFICATION")
    print("-" * 40)
    database_correct = tester.test_cancelled_orders_in_database()
    
    # Results
    print("\n" + "=" * 80)
    print("📊 URGENT INVESTIGATION RESULTS")
    print("=" * 80)
    
    print(f"1. /api/admin/orders/{{order_id}}/cancel endpoint: {'✅ WORKING' if cancel_endpoint_works else '❌ FAILING'}")
    print(f"2. /api/admin/orders/{{order_id}}/status with 'cancelled': {'✅ WORKING' if status_endpoint_works else '❌ FAILING'}")
    print(f"3. Database persistence of cancelled orders: {'✅ WORKING' if database_correct else '❌ FAILING'}")
    
    print(f"\n🎯 SUMMARY:")
    if cancel_endpoint_works and status_endpoint_works and database_correct:
        print("✅ ALL BACKEND CANCELLATION FUNCTIONALITY IS WORKING CORRECTLY")
        print("🔍 The issue is likely in the FRONTEND implementation")
        print("💡 The admin interface may not be calling the correct endpoints")
    else:
        print("❌ BACKEND ISSUES DETECTED:")
        if not cancel_endpoint_works:
            print("   - Cancel endpoint not working properly")
        if not status_endpoint_works:
            print("   - Status endpoint not handling 'cancelled' correctly")
        if not database_correct:
            print("   - Database persistence issues with cancelled orders")
    
    print(f"\n📋 RECOMMENDATIONS:")
    print("1. Check frontend AdminDashboard.js for correct API calls")
    print("2. Verify frontend is using the correct endpoints:")
    print("   - PUT /api/admin/orders/{order_id}/cancel (sets price to 0)")
    print("   - PUT /api/admin/orders/{order_id}/status (for status changes)")
    print("3. Check frontend error handling and user feedback")

if __name__ == "__main__":
    main()