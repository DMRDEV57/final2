#!/usr/bin/env python3

import requests
import json
from datetime import datetime

class UrgentDiagnosisTest:
    def __init__(self):
        self.base_url = "https://ba7542fd-fff4-49dc-8761-c0598ae50777.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.admin_token = None

    def test_admin_login(self):
        """Test admin login with admin@test.com / admin123"""
        print("🔍 TESTING ADMIN LOGIN...")
        url = f"{self.api_url}/auth/login"
        data = {"email": "admin@test.com", "password": "admin123"}
        
        try:
            response = requests.post(url, json=data)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.admin_token = result.get('access_token')
                print("   ✅ Admin login SUCCESSFUL")
                return True
            else:
                print(f"   ❌ Admin login FAILED")
                try:
                    error = response.json()
                    print(f"   Error: {error}")
                except:
                    print(f"   Error: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            return False

    def test_get_admin_users(self):
        """Test retrieving existing users"""
        print("\n🔍 TESTING GET EXISTING USERS...")
        if not self.admin_token:
            print("   ❌ No admin token available")
            return False
            
        url = f"{self.api_url}/admin/users"
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        try:
            response = requests.get(url, headers=headers)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                users = response.json()
                print(f"   ✅ Retrieved {len(users)} users")
                
                # Check admin user structure
                admin_user = None
                for user in users:
                    if user.get('email') == 'admin@test.com':
                        admin_user = user
                        break
                
                if admin_user:
                    print(f"   📋 Admin user found:")
                    print(f"      - Email: {admin_user.get('email')}")
                    print(f"      - Phone: {admin_user.get('phone', 'MISSING')}")
                    print(f"      - Country: {admin_user.get('country', 'MISSING')}")
                    print(f"      - Role: {admin_user.get('role')}")
                    
                    # Check if phone/country are missing
                    missing_phone = admin_user.get('phone') is None
                    missing_country = admin_user.get('country') is None
                    
                    if missing_phone or missing_country:
                        print(f"   🚨 PROBLEM IDENTIFIED: Admin user missing required fields!")
                        print(f"      - Missing phone: {missing_phone}")
                        print(f"      - Missing country: {missing_country}")
                        return False
                    else:
                        print(f"   ✅ Admin user has all required fields")
                        return True
                else:
                    print(f"   ❌ Admin user not found in database")
                    return False
            else:
                print(f"   ❌ Failed to get users")
                try:
                    error = response.json()
                    print(f"   Error: {error}")
                except:
                    print(f"   Error: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            return False

    def test_create_new_user(self):
        """Test creating a new user with phone and country"""
        print("\n🔍 TESTING CREATE NEW USER...")
        
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "email": f"test_user_{timestamp}@example.com",
            "password": "TestPass123!",
            "first_name": "Test",
            "last_name": "User",
            "phone": "0123456789",  # Required field
            "country": "France",    # Required field
            "company": "Test Company"
        }
        
        url = f"{self.api_url}/auth/register"
        
        try:
            response = requests.post(url, json=user_data)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("   ✅ User creation SUCCESSFUL")
                print(f"   📋 Created user: {result.get('email')}")
                return True
            else:
                print(f"   ❌ User creation FAILED")
                try:
                    error = response.json()
                    print(f"   Error: {error}")
                    
                    # Check for validation errors
                    if 'detail' in error and isinstance(error['detail'], list):
                        for detail in error['detail']:
                            if detail.get('type') == 'missing':
                                field = detail.get('loc', [])[-1] if detail.get('loc') else 'unknown'
                                print(f"   🚨 Missing required field: {field}")
                except:
                    print(f"   Error: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            return False

    def test_create_user_without_phone_country(self):
        """Test creating user without phone/country to confirm validation"""
        print("\n🔍 TESTING CREATE USER WITHOUT PHONE/COUNTRY...")
        
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "email": f"test_incomplete_{timestamp}@example.com",
            "password": "TestPass123!",
            "first_name": "Incomplete",
            "last_name": "User",
            # Missing phone and country intentionally
        }
        
        url = f"{self.api_url}/auth/register"
        
        try:
            response = requests.post(url, json=user_data)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 422:  # Validation error expected
                error = response.json()
                print("   ✅ Validation working correctly (422 error expected)")
                
                missing_fields = []
                if 'detail' in error and isinstance(error['detail'], list):
                    for detail in error['detail']:
                        if detail.get('type') == 'missing':
                            field = detail.get('loc', [])[-1] if detail.get('loc') else 'unknown'
                            missing_fields.append(field)
                
                print(f"   📋 Missing fields detected: {missing_fields}")
                
                # Check if phone and country are in missing fields
                phone_missing = 'phone' in missing_fields
                country_missing = 'country' in missing_fields
                
                print(f"   🔍 Phone field validation: {'✅' if phone_missing else '❌'}")
                print(f"   🔍 Country field validation: {'✅' if country_missing else '❌'}")
                
                return phone_missing and country_missing
            else:
                print(f"   ❌ Expected validation error (422), got {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            return False

    def test_admin_endpoints_with_missing_fields(self):
        """Test admin endpoints that might fail due to missing user fields"""
        print("\n🔍 TESTING ADMIN ENDPOINTS...")
        if not self.admin_token:
            print("   ❌ No admin token available")
            return False
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Test admin/users endpoint
        print("   Testing /admin/users...")
        try:
            response = requests.get(f"{self.api_url}/admin/users", headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code != 200:
                try:
                    error = response.json()
                    print(f"   Error: {error}")
                except:
                    print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Exception: {str(e)}")
        
        # Test admin/orders endpoint
        print("   Testing /admin/orders...")
        try:
            response = requests.get(f"{self.api_url}/admin/orders", headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code != 200:
                try:
                    error = response.json()
                    print(f"   Error: {error}")
                except:
                    print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Exception: {str(e)}")
        
        # Test admin/chat/conversations endpoint
        print("   Testing /admin/chat/conversations...")
        try:
            response = requests.get(f"{self.api_url}/admin/chat/conversations", headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code != 200:
                try:
                    error = response.json()
                    print(f"   Error: {error}")
                except:
                    print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Exception: {str(e)}")

def main():
    print("🚨 URGENT DIAGNOSIS - CONNECTION ISSUES")
    print("=" * 60)
    print("Testing specific issues mentioned in review request:")
    print("1. Admin login with admin@test.com / admin123")
    print("2. Creating new users")
    print("3. Phone and country field requirements")
    print("4. Retrieving existing users")
    print("=" * 60)
    
    tester = UrgentDiagnosisTest()
    
    # Run diagnostic tests
    print("\n📋 DIAGNOSTIC TEST SEQUENCE:")
    
    # Test 1: Admin login
    admin_login_success = tester.test_admin_login()
    
    # Test 2: Get existing users (check for missing fields)
    if admin_login_success:
        users_success = tester.test_get_admin_users()
    else:
        users_success = False
    
    # Test 3: Create new user with required fields
    new_user_success = tester.test_create_new_user()
    
    # Test 4: Validate phone/country requirements
    validation_success = tester.test_create_user_without_phone_country()
    
    # Test 5: Check admin endpoints
    if admin_login_success:
        tester.test_admin_endpoints_with_missing_fields()
    
    # Summary
    print("\n" + "=" * 60)
    print("🔍 DIAGNOSIS SUMMARY:")
    print("=" * 60)
    print(f"1. Admin login: {'✅ WORKING' if admin_login_success else '❌ FAILED'}")
    print(f"2. Get existing users: {'✅ WORKING' if users_success else '❌ FAILED'}")
    print(f"3. Create new user: {'✅ WORKING' if new_user_success else '❌ FAILED'}")
    print(f"4. Field validation: {'✅ WORKING' if validation_success else '❌ FAILED'}")
    
    print("\n🎯 ROOT CAUSE ANALYSIS:")
    if not users_success and admin_login_success:
        print("❌ PROBLEM: Admin user in database missing required phone/country fields")
        print("   This causes User model validation to fail when retrieving users")
        print("   Solution: Update admin user in database to include phone and country")
    elif not admin_login_success:
        print("❌ PROBLEM: Admin login failing")
        print("   Check if admin user exists and password is correct")
    elif not new_user_success:
        print("❌ PROBLEM: New user creation failing")
        print("   Check validation requirements and field mappings")
    else:
        print("✅ All basic functionality working correctly")

if __name__ == "__main__":
    main()