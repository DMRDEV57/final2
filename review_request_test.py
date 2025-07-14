#!/usr/bin/env python3

import requests
import sys
import json
import io
from datetime import datetime

class ReviewRequestTester:
    def __init__(self, base_url="https://ba7542fd-fff4-49dc-8761-c0598ae50777.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.client_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_orders = []  # Track created orders for testing

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
                    test_headers.pop('Content-Type', None)
                    response = requests.post(url, data=data, files=files, headers=test_headers)
                elif form_data:
                    test_headers.pop('Content-Type', None)
                    response = requests.post(url, data=data, headers=test_headers)
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
        print("🔐 Setting up authentication...")
        
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
            "email": f"review_test_client_{timestamp}@example.com",
            "password": "TestPass123!",
            "first_name": "Review",
            "last_name": "TestClient",
            "phone": "0123456789",
            "company": "Review Test Company"
        }
        
        success, response = self.run_test(
            "Client Registration",
            "POST",
            "auth/register",
            200,
            data=client_data
        )
        
        if success:
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

    def create_test_orders(self):
        """Create test orders with different statuses"""
        print("\n📋 Creating test orders...")
        
        if not self.client_token:
            print("❌ Cannot create orders - missing client token")
            return False

        # Get services first
        success, services = self.run_test(
            "Get Services for Order Creation",
            "GET",
            "services",
            200
        )
        
        if not success or not services:
            print("❌ Cannot get services")
            return False

        service_id = services[0]['id']
        headers = {'Authorization': f'Bearer {self.client_token}'}
        
        # Create multiple test orders
        order_types = [
            {"name": "Pending Order", "status": "pending"},
            {"name": "Processing Order", "status": "processing"},
            {"name": "Completed Order", "status": "completed"},
            {"name": "Cancelled Order", "status": "cancelled"}
        ]
        
        for order_type in order_types:
            # Create order
            success, response = self.run_test(
                f"Create {order_type['name']}",
                "POST",
                "orders",
                200,
                data={"service_id": service_id},
                headers=headers
            )
            
            if success and 'id' in response:
                order_id = response['id']
                original_price = response.get('price', 0)
                
                # Update status if not pending
                if order_type['status'] != 'pending':
                    admin_headers = {'Authorization': f'Bearer {self.admin_token}'}
                    status_success, status_response = self.run_test(
                        f"Set {order_type['name']} Status to {order_type['status']}",
                        "PUT",
                        f"admin/orders/{order_id}/status",
                        200,
                        data={"status": order_type['status']},
                        headers=admin_headers
                    )
                    
                    if status_success:
                        print(f"   ✅ Order {order_id} set to {order_type['status']}")
                
                self.test_orders.append({
                    'id': order_id,
                    'status': order_type['status'],
                    'name': order_type['name'],
                    'original_price': original_price
                })
        
        print(f"✅ Created {len(self.test_orders)} test orders")
        return len(self.test_orders) > 0

    def test_pending_orders_excludes_completed_cancelled(self):
        """REVIEW REQUEST TEST 1: Test that /api/admin/orders/pending excludes completed and cancelled orders"""
        print("\n🎯 REVIEW REQUEST TEST 1: Pending orders should exclude completed/cancelled")
        
        if not self.admin_token:
            print("❌ Cannot test - missing admin token")
            return False

        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success, pending_orders = self.run_test(
            "Get Pending Orders (Should exclude completed/cancelled)",
            "GET",
            "admin/orders/pending",
            200,
            headers=headers
        )
        
        if not success:
            return False

        print(f"   📋 Found {len(pending_orders)} pending orders")
        
        # Check that no completed or cancelled orders are in the list
        excluded_statuses = ['completed', 'cancelled']
        invalid_orders = []
        
        for order in pending_orders:
            order_status = order.get('status', 'unknown')
            if order_status in excluded_statuses:
                invalid_orders.append({
                    'id': order.get('id', 'unknown'),
                    'status': order_status
                })
        
        if invalid_orders:
            print(f"   ❌ FAILED: Found {len(invalid_orders)} orders with excluded statuses:")
            for invalid_order in invalid_orders:
                print(f"      - Order {invalid_order['id']}: status '{invalid_order['status']}'")
            return False
        else:
            print(f"   ✅ SUCCESS: No completed or cancelled orders found in pending list")
            
            # Show what statuses are present
            statuses_found = set(order.get('status', 'unknown') for order in pending_orders)
            print(f"   📊 Statuses in pending orders: {', '.join(statuses_found) if statuses_found else 'None'}")
            return True

    def test_cancel_order_functionality(self):
        """REVIEW REQUEST TEST 2: Test that cancel order endpoint works correctly"""
        print("\n🎯 REVIEW REQUEST TEST 2: Cancel order functionality")
        
        if not self.admin_token or not self.test_orders:
            print("❌ Cannot test - missing admin token or test orders")
            return False

        # Find a non-cancelled order to cancel
        order_to_cancel = None
        for order in self.test_orders:
            if order['status'] != 'cancelled':
                order_to_cancel = order
                break
        
        if not order_to_cancel:
            print("❌ No suitable order found to cancel")
            return False

        order_id = order_to_cancel['id']
        original_price = order_to_cancel['original_price']
        
        print(f"   🎯 Cancelling order {order_id} (original price: {original_price}€)")
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success, response = self.run_test(
            "Cancel Order",
            "PUT",
            f"admin/orders/{order_id}/cancel",
            200,
            headers=headers
        )
        
        if not success:
            return False

        # Verify the order was cancelled and price set to 0
        verify_success, all_orders = self.run_test(
            "Verify Order Cancelled",
            "GET",
            "admin/orders",
            200,
            headers=headers
        )
        
        if verify_success:
            cancelled_order = None
            for order in all_orders:
                if order['id'] == order_id:
                    cancelled_order = order
                    break
            
            if cancelled_order:
                new_status = cancelled_order.get('status', 'unknown')
                new_price = cancelled_order.get('price', -1)
                cancelled_at = cancelled_order.get('cancelled_at')
                
                print(f"   📊 Order after cancellation:")
                print(f"      Status: {new_status}")
                print(f"      Price: {new_price}€ (was {original_price}€)")
                print(f"      Cancelled at: {cancelled_at}")
                
                if new_status == 'cancelled' and new_price == 0.0 and cancelled_at:
                    print(f"   ✅ SUCCESS: Order correctly cancelled with price set to 0")
                    return True
                else:
                    print(f"   ❌ FAILED: Order not properly cancelled")
                    print(f"      Expected: status='cancelled', price=0.0, cancelled_at=not null")
                    print(f"      Got: status='{new_status}', price={new_price}, cancelled_at={cancelled_at}")
                    return False
            else:
                print(f"   ❌ FAILED: Could not find cancelled order in response")
                return False
        
        return False

    def test_completed_order_not_in_pending(self):
        """REVIEW REQUEST TEST 3: Create order, set to completed, verify not in pending"""
        print("\n🎯 REVIEW REQUEST TEST 3: Completed order should not appear in pending")
        
        if not self.admin_token or not self.client_token:
            print("❌ Cannot test - missing tokens")
            return False

        # Get services
        success, services = self.run_test(
            "Get Services for Completed Order Test",
            "GET",
            "services",
            200
        )
        
        if not success or not services:
            print("❌ Cannot get services")
            return False

        # Create new order
        service_id = services[0]['id']
        client_headers = {'Authorization': f'Bearer {self.client_token}'}
        
        success, new_order = self.run_test(
            "Create Order for Completion Test",
            "POST",
            "orders",
            200,
            data={"service_id": service_id},
            headers=client_headers
        )
        
        if not success or 'id' not in new_order:
            print("❌ Failed to create test order")
            return False

        order_id = new_order['id']
        print(f"   📋 Created test order: {order_id}")

        # Set order to completed
        admin_headers = {'Authorization': f'Bearer {self.admin_token}'}
        success, response = self.run_test(
            "Set Order to Completed",
            "PUT",
            f"admin/orders/{order_id}/status",
            200,
            data={"status": "completed", "admin_notes": "Test completion for review request"},
            headers=admin_headers
        )
        
        if not success:
            print("❌ Failed to set order to completed")
            return False

        print(f"   ✅ Order {order_id} set to completed")

        # Check that it doesn't appear in pending orders
        success, pending_orders = self.run_test(
            "Get Pending Orders (Should not include completed order)",
            "GET",
            "admin/orders/pending",
            200,
            headers=admin_headers
        )
        
        if not success:
            return False

        # Check if our completed order is in the pending list
        completed_order_in_pending = any(order.get('id') == order_id for order in pending_orders)
        
        if completed_order_in_pending:
            print(f"   ❌ FAILED: Completed order {order_id} found in pending orders list")
            return False
        else:
            print(f"   ✅ SUCCESS: Completed order {order_id} correctly excluded from pending orders")
            return True

    def test_status_harmonization(self):
        """REVIEW REQUEST TEST 4: Test status harmonization uses 'completed' not 'terminé'"""
        print("\n🎯 REVIEW REQUEST TEST 4: Status harmonization (completed vs terminé)")
        
        if not self.admin_token:
            print("❌ Cannot test - missing admin token")
            return False

        # Find a pending order to test with
        pending_order = None
        for order in self.test_orders:
            if order['status'] == 'pending':
                pending_order = order
                break
        
        if not pending_order:
            print("❌ No pending order found for status test")
            return False

        order_id = pending_order['id']
        admin_headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Test setting status to 'completed' (harmonized status)
        success, response = self.run_test(
            "Set Order Status to 'completed' (harmonized)",
            "PUT",
            f"admin/orders/{order_id}/status",
            200,
            data={"status": "completed", "admin_notes": "Testing status harmonization"},
            headers=admin_headers
        )
        
        if not success:
            return False

        # Verify the status was set correctly
        success, all_orders = self.run_test(
            "Verify Status Harmonization",
            "GET",
            "admin/orders",
            200,
            headers=admin_headers
        )
        
        if success:
            test_order = None
            for order in all_orders:
                if order['id'] == order_id:
                    test_order = order
                    break
            
            if test_order:
                status = test_order.get('status', 'unknown')
                completed_at = test_order.get('completed_at')
                
                print(f"   📊 Order status after update: '{status}'")
                print(f"   📅 Completed at: {completed_at}")
                
                if status == 'completed' and completed_at:
                    print(f"   ✅ SUCCESS: Status correctly set to 'completed' with timestamp")
                    return True
                else:
                    print(f"   ❌ FAILED: Expected status='completed' with completed_at timestamp")
                    return False
        
        return False

    def run_all_tests(self):
        """Run all review request tests"""
        print("🚀 Starting Review Request Tests")
        print("=" * 60)
        
        # Setup
        if not self.setup_authentication():
            print("❌ Authentication setup failed")
            return False
        
        if not self.create_test_orders():
            print("❌ Test order creation failed")
            return False
        
        # Run specific review request tests
        tests = [
            ("Pending Orders Exclude Completed/Cancelled", self.test_pending_orders_excludes_completed_cancelled),
            ("Cancel Order Functionality", self.test_cancel_order_functionality),
            ("Completed Order Not in Pending", self.test_completed_order_not_in_pending),
            ("Status Harmonization", self.test_status_harmonization),
        ]
        
        print(f"\n🎯 REVIEW REQUEST SPECIFIC TESTS:")
        print("-" * 40)
        
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                test_func()
            except Exception as e:
                print(f"❌ Test failed with exception: {str(e)}")
        
        # Print final results
        print(f"\n{'='*60}")
        print(f"📊 REVIEW REQUEST TEST RESULTS")
        print(f"{'='*60}")
        print(f"Tests passed: {self.tests_passed}/{self.tests_run}")
        print(f"Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.test_orders:
            print(f"\n📋 TEST ORDERS CREATED:")
            for order in self.test_orders:
                print(f"  - {order['name']}: {order['id']} (status: {order['status']})")
        
        return self.tests_passed == self.tests_run

def main():
    tester = ReviewRequestTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All review request tests passed!")
        return 0
    else:
        print(f"\n⚠️ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())