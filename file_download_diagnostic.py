#!/usr/bin/env python3

import requests
import sys
import json
import io
from datetime import datetime
import gridfs
from pymongo import MongoClient
import os
from dotenv import load_dotenv

class FileDownloadDiagnostic:
    def __init__(self, base_url="https://ba7542fd-fff4-49dc-8761-c0598ae50777.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.client_token = None
        self.client_user_id = None
        self.service_id = None
        self.order_id = None
        self.uploaded_files = []
        
        # MongoDB connection for direct GridFS inspection
        load_dotenv('/app/backend/.env')
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.environ.get('DB_NAME', 'test_database')
        self.mongo_client = MongoClient(mongo_url)
        self.db = self.mongo_client[db_name]
        self.fs = gridfs.GridFS(self.db)

    def log(self, message, level="INFO"):
        """Enhanced logging with levels"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {level}: {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, files=None, form_data=False):
        """Run a single API test with enhanced error reporting"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if headers:
            test_headers.update(headers)

        self.log(f"Testing {name}...")
        self.log(f"URL: {url}", "DEBUG")
        
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
                self.log(f"✅ {name} - Status: {response.status_code}", "SUCCESS")
                try:
                    if 'application/json' in response.headers.get('content-type', ''):
                        response_data = response.json()
                        self.log(f"Response: {json.dumps(response_data, indent=2)[:200]}...", "DEBUG")
                        return True, response_data
                    else:
                        # For file downloads, return response object
                        return True, response
                except:
                    return True, response
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}", "ERROR")
                self.log(f"Response headers: {dict(response.headers)}", "DEBUG")
                try:
                    error_data = response.json()
                    self.log(f"Error: {error_data}", "ERROR")
                except:
                    self.log(f"Error text: {response.text}", "ERROR")
                return False, response

        except Exception as e:
            self.log(f"❌ {name} - Exception: {str(e)}", "ERROR")
            return False, {}

    def setup_authentication(self):
        """Setup admin and client authentication"""
        self.log("=== AUTHENTICATION SETUP ===")
        
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
            self.log("✅ Admin authentication successful")
        else:
            self.log("❌ Admin authentication failed", "ERROR")
            return False

        # Client registration and login
        timestamp = datetime.now().strftime('%H%M%S')
        client_data = {
            "email": f"test_client_{timestamp}@example.com",
            "password": "TestPass123!",
            "first_name": "Test",
            "last_name": "Client",
            "phone": "0123456789",
            "country": "France",
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
            
            # Login with new client
            login_success, login_response = self.run_test(
                "Client Login",
                "POST",
                "auth/login",
                200,
                data={"email": client_data["email"], "password": client_data["password"]}
            )
            if login_success and 'access_token' in login_response:
                self.client_token = login_response['access_token']
                self.log("✅ Client authentication successful")
                return True
        
        self.log("❌ Client authentication failed", "ERROR")
        return False

    def setup_order_with_files(self):
        """Create an order and upload files for testing"""
        self.log("=== ORDER AND FILE SETUP ===")
        
        # Get services
        success, response = self.run_test(
            "Get Services",
            "GET",
            "services",
            200
        )
        if success and len(response) > 0:
            self.service_id = response[0]['id']
            self.log(f"✅ Service ID obtained: {self.service_id}")
        else:
            self.log("❌ Failed to get services", "ERROR")
            return False

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
            self.log(f"✅ Order created: {self.order_id}")
        else:
            self.log("❌ Failed to create order", "ERROR")
            return False

        # Upload client file
        test_file_content = b"This is a test cartography file for download testing - BMW 320d Stage 1"
        test_file = io.BytesIO(test_file_content)
        test_notes = "Vehicle: BMW 320d 2018, Immatriculation: AB-123-CD, Current: Stock, Requested: Stage 1"
        
        files = {'file': ('test_cartography.bin', test_file, 'application/octet-stream')}
        form_data = {'notes': test_notes}
        
        success, response = self.run_test(
            "Upload Client File",
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
                'uploaded_by': 'client'
            })
            self.log(f"✅ Client file uploaded: {response['file_id']}")
        else:
            self.log("❌ Failed to upload client file", "ERROR")
            return False

        # Upload admin file
        admin_file_content = b"This is a modified cartography file - Stage 1 tuning applied by admin"
        admin_file = io.BytesIO(admin_file_content)
        admin_notes = "Applied Stage 1 tuning, increased boost pressure, optimized fuel mapping"
        
        admin_headers = {'Authorization': f'Bearer {self.admin_token}'}
        files = {'file': ('modified_cartography_v1.bin', admin_file, 'application/octet-stream')}
        form_data = {
            'version_type': 'v1',
            'notes': admin_notes
        }
        
        success, response = self.run_test(
            "Upload Admin File",
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
                'version_type': 'v1',
                'uploaded_by': 'admin'
            })
            self.log(f"✅ Admin file uploaded: {response['file_id']}")
        else:
            self.log("❌ Failed to upload admin file", "ERROR")

        return len(self.uploaded_files) > 0

    def inspect_gridfs_directly(self):
        """Direct inspection of GridFS to check if files are stored correctly"""
        self.log("=== DIRECT GRIDFS INSPECTION ===")
        
        try:
            # List all files in GridFS
            files_in_gridfs = list(self.fs.find())
            self.log(f"📁 Total files in GridFS: {len(files_in_gridfs)}")
            
            for i, file_doc in enumerate(files_in_gridfs):
                self.log(f"File {i+1}:")
                self.log(f"  - ID: {file_doc._id}")
                self.log(f"  - Filename: {file_doc.filename}")
                self.log(f"  - Content Type: {file_doc.content_type}")
                self.log(f"  - Length: {file_doc.length} bytes")
                self.log(f"  - Upload Date: {file_doc.uploadDate}")
                
                # Try to read a small portion of the file
                try:
                    file_content = file_doc.read(100)  # Read first 100 bytes
                    self.log(f"  - Content preview: {file_content[:50]}...")
                    file_doc.seek(0)  # Reset file pointer
                except Exception as e:
                    self.log(f"  - Error reading content: {e}", "ERROR")
            
            # Check if our uploaded files are in GridFS
            for uploaded_file in self.uploaded_files:
                file_id = uploaded_file['file_id']
                self.log(f"🔍 Checking uploaded file {file_id} in GridFS...")
                
                try:
                    # Try to find by ObjectId
                    from bson import ObjectId
                    try:
                        grid_file = self.fs.get(ObjectId(file_id))
                        self.log(f"  ✅ Found by ObjectId: {grid_file.filename}")
                    except:
                        # Try to find by string ID
                        grid_file = self.fs.get(file_id)
                        self.log(f"  ✅ Found by string ID: {grid_file.filename}")
                    
                    # Test reading the file
                    content = grid_file.read()
                    self.log(f"  ✅ File readable, size: {len(content)} bytes")
                    
                except Exception as e:
                    self.log(f"  ❌ File not found or not readable: {e}", "ERROR")
            
            return len(files_in_gridfs) > 0
            
        except Exception as e:
            self.log(f"❌ GridFS inspection failed: {e}", "ERROR")
            return False

    def test_file_metadata_retrieval(self):
        """Test retrieving file metadata from order"""
        self.log("=== FILE METADATA RETRIEVAL TEST ===")
        
        headers = {'Authorization': f'Bearer {self.client_token}'}
        success, response = self.run_test(
            "Get Order with Files",
            "GET",
            "orders",
            200,
            headers=headers
        )
        
        if success and isinstance(response, list):
            test_order = None
            for order in response:
                if order['id'] == self.order_id:
                    test_order = order
                    break
            
            if test_order:
                files_info = test_order.get('files', [])
                self.log(f"📁 Found {len(files_info)} files in order metadata:")
                
                for i, file_info in enumerate(files_info):
                    self.log(f"File {i+1}:")
                    self.log(f"  - File ID: {file_info.get('file_id', 'N/A')}")
                    self.log(f"  - Filename: {file_info.get('filename', 'N/A')}")
                    self.log(f"  - Version Type: {file_info.get('version_type', 'N/A')}")
                    self.log(f"  - Uploaded By: {file_info.get('uploaded_by', 'N/A')}")
                    self.log(f"  - Upload Date: {file_info.get('uploaded_at', 'N/A')}")
                    self.log(f"  - Notes: {file_info.get('notes', 'N/A')[:50]}...")
                
                return len(files_info) > 0
            else:
                self.log("❌ Test order not found in response", "ERROR")
                return False
        else:
            self.log("❌ Failed to retrieve orders", "ERROR")
            return False

    def test_client_download_endpoints(self):
        """Test client file download endpoints"""
        self.log("=== CLIENT DOWNLOAD ENDPOINTS TEST ===")
        
        if not self.uploaded_files:
            self.log("❌ No uploaded files to test download", "ERROR")
            return False
        
        headers = {'Authorization': f'Bearer {self.client_token}'}
        
        for i, file_info in enumerate(self.uploaded_files):
            file_id = file_info['file_id']
            filename = file_info['filename']
            
            self.log(f"🔽 Testing download {i+1}: {filename} (ID: {file_id})")
            
            success, response = self.run_test(
                f"Client Download File {i+1}",
                "GET",
                f"orders/{self.order_id}/download/{file_id}",
                200,
                headers=headers
            )
            
            if success:
                # Check response headers
                content_type = response.headers.get('content-type', 'N/A')
                content_disposition = response.headers.get('content-disposition', 'N/A')
                content_length = response.headers.get('content-length', 'N/A')
                
                self.log(f"  ✅ Download successful")
                self.log(f"  - Content-Type: {content_type}")
                self.log(f"  - Content-Disposition: {content_disposition}")
                self.log(f"  - Content-Length: {content_length}")
                
                # Try to read content
                try:
                    if hasattr(response, 'content'):
                        content = response.content
                        self.log(f"  - Content size: {len(content)} bytes")
                        self.log(f"  - Content preview: {content[:50]}...")
                    else:
                        self.log(f"  - Response type: {type(response)}")
                except Exception as e:
                    self.log(f"  - Error reading content: {e}", "ERROR")
            else:
                self.log(f"  ❌ Download failed for {filename}")
                # Additional debugging for failed downloads
                self.log(f"  - Status Code: {response.status_code}")
                self.log(f"  - Response Headers: {dict(response.headers)}")
                try:
                    error_content = response.text
                    self.log(f"  - Error Content: {error_content}")
                except:
                    pass
        
        return True

    def test_admin_download_endpoints(self):
        """Test admin file download endpoints"""
        self.log("=== ADMIN DOWNLOAD ENDPOINTS TEST ===")
        
        if not self.uploaded_files:
            self.log("❌ No uploaded files to test download", "ERROR")
            return False
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        for i, file_info in enumerate(self.uploaded_files):
            file_id = file_info['file_id']
            filename = file_info['filename']
            
            self.log(f"🔽 Testing admin download {i+1}: {filename} (ID: {file_id})")
            
            success, response = self.run_test(
                f"Admin Download File {i+1}",
                "GET",
                f"admin/orders/{self.order_id}/download/{file_id}",
                200,
                headers=headers
            )
            
            if success:
                # Check response headers
                content_type = response.headers.get('content-type', 'N/A')
                content_disposition = response.headers.get('content-disposition', 'N/A')
                content_length = response.headers.get('content-length', 'N/A')
                
                self.log(f"  ✅ Admin download successful")
                self.log(f"  - Content-Type: {content_type}")
                self.log(f"  - Content-Disposition: {content_disposition}")
                self.log(f"  - Content-Length: {content_length}")
                
                # Try to read content
                try:
                    if hasattr(response, 'content'):
                        content = response.content
                        self.log(f"  - Content size: {len(content)} bytes")
                        self.log(f"  - Content preview: {content[:50]}...")
                    else:
                        self.log(f"  - Response type: {type(response)}")
                except Exception as e:
                    self.log(f"  - Error reading content: {e}", "ERROR")
            else:
                self.log(f"  ❌ Admin download failed for {filename}")
                # Additional debugging for failed downloads
                self.log(f"  - Status Code: {response.status_code}")
                self.log(f"  - Response Headers: {dict(response.headers)}")
                try:
                    error_content = response.text
                    self.log(f"  - Error Content: {error_content}")
                except:
                    pass
        
        return True

    def test_download_with_invalid_ids(self):
        """Test download with invalid file IDs to check error handling"""
        self.log("=== INVALID ID DOWNLOAD TEST ===")
        
        headers = {'Authorization': f'Bearer {self.client_token}'}
        
        # Test with non-existent file ID
        invalid_ids = [
            "nonexistent123",
            "507f1f77bcf86cd799439011",  # Valid ObjectId format but non-existent
            "invalid-format-id"
        ]
        
        for invalid_id in invalid_ids:
            self.log(f"🔍 Testing invalid file ID: {invalid_id}")
            
            success, response = self.run_test(
                f"Download Invalid File ID",
                "GET",
                f"orders/{self.order_id}/download/{invalid_id}",
                404,  # Expect 404 for invalid file
                headers=headers
            )
            
            if success:
                self.log(f"  ✅ Correctly returned 404 for invalid ID")
            else:
                self.log(f"  ❌ Unexpected response for invalid ID")
                self.log(f"  - Status: {response.status_code}")
        
        return True

    def run_comprehensive_diagnosis(self):
        """Run comprehensive file download diagnosis"""
        self.log("🚀 STARTING COMPREHENSIVE FILE DOWNLOAD DIAGNOSIS")
        self.log("=" * 70)
        
        # Step 1: Setup
        if not self.setup_authentication():
            self.log("❌ Authentication setup failed - cannot continue", "ERROR")
            return False
        
        if not self.setup_order_with_files():
            self.log("❌ Order and file setup failed - cannot continue", "ERROR")
            return False
        
        # Step 2: Direct GridFS inspection
        self.inspect_gridfs_directly()
        
        # Step 3: File metadata retrieval
        self.test_file_metadata_retrieval()
        
        # Step 4: Client download tests
        self.test_client_download_endpoints()
        
        # Step 5: Admin download tests
        self.test_admin_download_endpoints()
        
        # Step 6: Invalid ID tests
        self.test_download_with_invalid_ids()
        
        self.log("=" * 70)
        self.log("🏁 FILE DOWNLOAD DIAGNOSIS COMPLETE")
        
        return True

def main():
    diagnostic = FileDownloadDiagnostic()
    diagnostic.run_comprehensive_diagnosis()

if __name__ == "__main__":
    main()