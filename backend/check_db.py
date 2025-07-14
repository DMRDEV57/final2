#!/usr/bin/env python3
"""
Script pour vérifier l'état de la base de données
Usage: python check_db.py
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
import json

# Add the backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# MongoDB connection
mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
db_name = os.getenv("MONGO_DB_NAME", "dmr_production_0f961c74")

client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

async def check_database_status():
    """Check database status and content"""
    print("🔍 DMR DÉVELOPPEMENT - Vérification de la base de données")
    print("=" * 60)
    
    # Check collections
    collections = await db.list_collection_names()
    print(f"📁 Collections: {collections}")
    
    # Check users
    users_count = await db.users.count_documents({})
    print(f"\n👥 Utilisateurs: {users_count}")
    
    if users_count > 0:
        async for user in db.users.find({}, {"password": 0}):  # Exclude password
            print(f"   - {user.get('email')} ({user.get('role')}) - {user.get('first_name')} {user.get('last_name')}")
    
    # Check services
    services_count = await db.services.count_documents({})
    print(f"\n🛠️  Services: {services_count}")
    
    if services_count > 0:
        async for service in db.services.find({}):
            active_status = "✅ Actif" if service.get('active', True) else "❌ Inactif"
            print(f"   - {service.get('name')} - {service.get('price')}€ - {active_status}")
    
    # Check orders
    orders_count = await db.orders.count_documents({})
    print(f"\n📦 Commandes: {orders_count}")
    
    if orders_count > 0:
        async for order in db.orders.find({}).limit(5):  # Show first 5 orders
            print(f"   - {order.get('order_number')} - {order.get('service_name')} - {order.get('status')}")
    
    # Check notifications
    notifications_count = await db.notifications.count_documents({})
    print(f"\n🔔 Notifications: {notifications_count}")
    
    # Check chat messages
    chat_count = await db.chat_messages.count_documents({})
    print(f"\n💬 Messages de chat: {chat_count}")
    
    print(f"\n📊 Résumé:")
    print(f"   - Base de données: {db_name}")
    print(f"   - URL MongoDB: {mongo_url}")
    print(f"   - Collections actives: {len(collections)}")
    print(f"   - Prête pour production: {'✅' if users_count > 0 else '❌'}")

async def main():
    await check_database_status()
    client.close()

if __name__ == "__main__":
    asyncio.run(main())