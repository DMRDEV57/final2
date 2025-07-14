#!/usr/bin/env python3

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent / "backend"
load_dotenv(ROOT_DIR / '.env')

async def fix_database():
    # MongoDB connection
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🔧 FIXING DATABASE - Adding missing phone/country fields to users")
    print("=" * 60)
    
    # Get all users
    users = await db.users.find({}).to_list(1000)
    print(f"📋 Found {len(users)} users in database")
    
    # Check and fix each user
    fixed_count = 0
    for user in users:
        email = user.get('email', 'unknown')
        needs_update = False
        update_data = {}
        
        # Check phone field
        if user.get('phone') is None:
            update_data['phone'] = "0000000000"  # Default phone
            needs_update = True
            print(f"   📞 Adding phone to user: {email}")
        
        # Check country field
        if user.get('country') is None:
            update_data['country'] = "France"  # Default country
            needs_update = True
            print(f"   🌍 Adding country to user: {email}")
        
        # Update user if needed
        if needs_update:
            await db.users.update_one(
                {"_id": user["_id"]},
                {"$set": update_data}
            )
            fixed_count += 1
            print(f"   ✅ Updated user: {email}")
    
    print(f"\n📊 SUMMARY: Fixed {fixed_count} users")
    
    # Verify fix by trying to retrieve all users
    print("\n🔍 VERIFICATION: Testing user retrieval...")
    try:
        users_after = await db.users.find({}).to_list(1000)
        print(f"✅ Successfully retrieved {len(users_after)} users after fix")
        
        # Check admin user specifically
        admin_user = await db.users.find_one({"email": "admin@test.com"})
        if admin_user:
            print(f"📋 Admin user verification:")
            print(f"   - Email: {admin_user.get('email')}")
            print(f"   - Phone: {admin_user.get('phone')}")
            print(f"   - Country: {admin_user.get('country')}")
            print(f"   - Role: {admin_user.get('role')}")
        else:
            print("❌ Admin user not found")
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_database())