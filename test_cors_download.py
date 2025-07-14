#!/usr/bin/env python3
"""
Test CORS headers for file download endpoints
"""
import requests
import json
from urllib.parse import urljoin

# Configuration
BASE_URL = "https://d31407dd-32fd-423f-891b-c1a73cd42fb7.preview.emergentagent.com"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "admin123"

def login_admin():
    """Login as admin and get token"""
    login_url = urljoin(BASE_URL, "/api/auth/login")
    login_data = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    response = requests.post(login_url, json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def get_orders_with_files(token):
    """Get orders that have files for testing"""
    orders_url = urljoin(BASE_URL, "/api/admin/orders")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(orders_url, headers=headers)
    if response.status_code == 200:
        orders = response.json()
        
        # Find orders with files
        orders_with_files = []
        for order in orders:
            if "files" in order and order["files"]:
                for file_info in order["files"]:
                    if "file_id" in file_info:
                        orders_with_files.append({
                            "order_id": order["id"],
                            "file_id": file_info["file_id"],
                            "filename": file_info.get("filename", "unknown")
                        })
        
        return orders_with_files
    else:
        print(f"Failed to get orders: {response.status_code} - {response.text}")
        return []

def test_cors_headers_admin_download(token, order_id, file_id):
    """Test CORS headers on admin download endpoint"""
    download_url = urljoin(BASE_URL, f"/api/admin/orders/{order_id}/download/{file_id}")
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n🔍 Testing admin download: {download_url}")
    
    # Test actual download
    response = requests.get(download_url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    # Check for CORS headers
    cors_headers = {
        "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
        "Access-Control-Allow-Credentials": response.headers.get("Access-Control-Allow-Credentials"),
        "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
        "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers")
    }
    
    print(f"CORS Headers: {cors_headers}")
    
    # Verify expected CORS headers
    expected_origin = "https://d31407dd-32fd-423f-891b-c1a73cd42fb7.preview.emergentagent.com"
    cors_ok = True
    
    if cors_headers["Access-Control-Allow-Origin"] != expected_origin:
        print(f"❌ Wrong origin: expected {expected_origin}, got {cors_headers['Access-Control-Allow-Origin']}")
        cors_ok = False
    
    if cors_headers["Access-Control-Allow-Credentials"] != "true":
        print(f"❌ Wrong credentials: expected 'true', got {cors_headers['Access-Control-Allow-Credentials']}")
        cors_ok = False
    
    if cors_ok:
        print("✅ CORS headers are correct!")
    
    return response.status_code == 200 and cors_ok

def test_cors_headers_client_download(token, order_id, file_id):
    """Test CORS headers on client download endpoint"""
    download_url = urljoin(BASE_URL, f"/api/orders/{order_id}/download/{file_id}")
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n🔍 Testing client download: {download_url}")
    
    # Test actual download
    response = requests.get(download_url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    # Check for CORS headers
    cors_headers = {
        "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
        "Access-Control-Allow-Credentials": response.headers.get("Access-Control-Allow-Credentials"),
        "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
        "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers")
    }
    
    print(f"CORS Headers: {cors_headers}")
    
    # Verify expected CORS headers
    expected_origin = "https://d31407dd-32fd-423f-891b-c1a73cd42fb7.preview.emergentagent.com"
    cors_ok = True
    
    if cors_headers["Access-Control-Allow-Origin"] != expected_origin:
        print(f"❌ Wrong origin: expected {expected_origin}, got {cors_headers['Access-Control-Allow-Origin']}")
        cors_ok = False
    
    if cors_headers["Access-Control-Allow-Credentials"] != "true":
        print(f"❌ Wrong credentials: expected 'true', got {cors_headers['Access-Control-Allow-Credentials']}")
        cors_ok = False
    
    if cors_ok:
        print("✅ CORS headers are correct!")
    
    return response.status_code in [200, 404] and cors_ok  # 404 is OK if order doesn't belong to user

def main():
    print("🚀 Testing CORS headers for file download endpoints...")
    
    # Login
    token = login_admin()
    if not token:
        print("❌ Failed to login")
        return
    
    print("✅ Admin login successful")
    
    # Get orders with files
    orders_with_files = get_orders_with_files(token)
    if not orders_with_files:
        print("❌ No orders with files found")
        return
    
    print(f"✅ Found {len(orders_with_files)} orders with files")
    
    # Test first few orders
    test_count = min(3, len(orders_with_files))
    admin_success = 0
    client_success = 0
    
    for i in range(test_count):
        order_info = orders_with_files[i]
        print(f"\n📁 Testing file: {order_info['filename']}")
        
        # Test admin download
        if test_cors_headers_admin_download(token, order_info["order_id"], order_info["file_id"]):
            admin_success += 1
        
        # Test client download (might fail if order doesn't belong to admin user)
        if test_cors_headers_client_download(token, order_info["order_id"], order_info["file_id"]):
            client_success += 1
    
    print(f"\n📊 Results:")
    print(f"Admin downloads with CORS: {admin_success}/{test_count}")
    print(f"Client downloads with CORS: {client_success}/{test_count}")
    
    if admin_success == test_count:
        print("✅ CORS corrections are working for admin downloads!")
    else:
        print("❌ CORS issues remain for admin downloads")

if __name__ == "__main__":
    main()