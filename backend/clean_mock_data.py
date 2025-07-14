#!/usr/bin/env python3
"""
Script pour nettoyer toutes les données fictives de la base de données
Usage: python clean_mock_data.py
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
import gridfs
from pymongo import MongoClient
import re

# Add the backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# MongoDB connection
mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
db_name = os.getenv("MONGO_DB_NAME", "dmr_production_0f961c74")

client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# GridFS for file cleanup
sync_client = MongoClient(mongo_url)
sync_db = sync_client[db_name]
fs = gridfs.GridFS(sync_db)

async def clean_mock_data():
    """Clean all mock/test data from database"""
    print("🧹 DMR DÉVELOPPEMENT - Nettoyage des données fictives")
    print("=" * 60)
    
    # Define patterns to identify mock/test data
    test_patterns = [
        'test', 'dummy', 'fake', 'sample', 'mock', 'example',
        'stage1', 'stage2', 'stage3', 'cartomapping', 'admin123'
    ]
    
    total_deleted = 0
    
    # 1. Clean test users (keep only real users)
    print("🗑️  Nettoyage des utilisateurs de test...")
    test_users = []
    async for user in db.users.find({}):
        email = user.get('email', '').lower()
        first_name = user.get('first_name', '').lower()
        last_name = user.get('last_name', '').lower()
        
        # Skip if it's a real admin user that should be kept
        if user.get('role') == 'admin' and not any(pattern in email for pattern in ['test', 'dummy', 'fake', 'sample', 'cartomapping']):
            continue
            
        # Check if user matches test patterns
        if any(pattern in email for pattern in test_patterns) or \
           any(pattern in first_name for pattern in test_patterns) or \
           any(pattern in last_name for pattern in test_patterns) or \
           'example.com' in email or 'test.com' in email:
            test_users.append(user)
    
    for user in test_users:
        await db.users.delete_one({"id": user["id"]})
        print(f"   ❌ Supprimé utilisateur: {user['email']}")
        total_deleted += 1
    
    # 2. Clean test services
    print("🗑️  Nettoyage des services de test...")
    test_services = []
    async for service in db.services.find({}):
        name = service.get('name', '').lower()
        description = service.get('description', '').lower()
        
        if any(pattern in name for pattern in test_patterns) or \
           any(pattern in description for pattern in test_patterns):
            test_services.append(service)
    
    for service in test_services:
        await db.services.delete_one({"id": service["id"]})
        print(f"   ❌ Supprimé service: {service['name']}")
        total_deleted += 1
    
    # 3. Clean test orders
    print("🗑️  Nettoyage des commandes de test...")
    test_orders = []
    async for order in db.orders.find({}):
        service_name = order.get('service_name', '').lower()
        user_id = order.get('user_id', '')
        
        # Check if order belongs to test user
        user = await db.users.find_one({"id": user_id})
        if not user:  # Orphaned order
            test_orders.append(order)
            continue
            
        # Check if service name suggests test data
        if any(pattern in service_name for pattern in test_patterns):
            test_orders.append(order)
    
    # Clean associated files from GridFS
    for order in test_orders:
        files = order.get('files', [])
        for file_info in files:
            file_id = file_info.get('file_id')
            if file_id:
                try:
                    fs.delete(file_id)
                    print(f"   🗂️  Supprimé fichier: {file_info.get('filename', 'Unknown')}")
                except Exception as e:
                    print(f"   ⚠️  Erreur suppression fichier {file_id}: {str(e)}")
        
        await db.orders.delete_one({"id": order["id"]})
        print(f"   ❌ Supprimé commande: {order.get('order_number', order['id'])}")
        total_deleted += 1
    
    # 4. Clean test notifications
    print("🗑️  Nettoyage des notifications de test...")
    test_notifications = []
    async for notification in db.notifications.find({}):
        message = notification.get('message', '').lower()
        title = notification.get('title', '').lower()
        
        if any(pattern in message for pattern in test_patterns) or \
           any(pattern in title for pattern in test_patterns):
            test_notifications.append(notification)
    
    for notification in test_notifications:
        await db.notifications.delete_one({"id": notification["id"]})
        print(f"   ❌ Supprimé notification: {notification.get('title', 'Unknown')}")
        total_deleted += 1
    
    # 5. Clean test chat messages
    print("🗑️  Nettoyage des messages de chat de test...")
    test_messages = []
    async for message in db.chat_messages.find({}):
        content = message.get('message', '').lower()
        
        if any(pattern in content for pattern in test_patterns):
            test_messages.append(message)
    
    for message in test_messages:
        await db.chat_messages.delete_one({"id": message["id"]})
        print(f"   ❌ Supprimé message: {message.get('message', 'Unknown')[:50]}...")
        total_deleted += 1
    
    # 6. Summary
    print("\n📊 Résumé du nettoyage:")
    print(f"   ✅ Total éléments supprimés: {total_deleted}")
    
    remaining_counts = {
        'users': await db.users.count_documents({}),
        'services': await db.services.count_documents({}),
        'orders': await db.orders.count_documents({}),
        'notifications': await db.notifications.count_documents({}),
        'chat_messages': await db.chat_messages.count_documents({})
    }
    
    print(f"   📋 Données restantes:")
    for collection, count in remaining_counts.items():
        print(f"      - {collection}: {count}")
    
    print(f"\n🎉 Nettoyage terminé! Base de données prête pour la production.")
    print(f"📝 Note: Vous devez maintenant créer des services et utilisateurs via l'interface d'administration.")

async def main():
    await clean_mock_data()
    client.close()
    sync_client.close()

if __name__ == "__main__":
    asyncio.run(main())