#!/usr/bin/env python3
"""
Script pour nettoyer complètement la base de données et la préparer pour la production
Usage: python final_cleanup.py
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
from datetime import datetime
import uuid

# Add the backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# MongoDB connection
mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
db_name = os.getenv("MONGO_DB_NAME", "dmr_production_0f961c74")

client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

async def final_cleanup():
    """Complete cleanup for production"""
    print("🧹 DMR DÉVELOPPEMENT - Nettoyage final pour la production")
    print("=" * 60)
    
    # 1. Remove ALL users (including duplicates)
    print("🗑️  Suppression de tous les utilisateurs...")
    users_deleted = await db.users.delete_many({})
    print(f"   ✅ {users_deleted.deleted_count} utilisateurs supprimés")
    
    # 2. Remove ALL services (including hardcoded ones)
    print("🗑️  Suppression de tous les services...")
    services_deleted = await db.services.delete_many({})
    print(f"   ✅ {services_deleted.deleted_count} services supprimés")
    
    # 3. Remove ALL orders
    print("🗑️  Suppression de toutes les commandes...")
    orders_deleted = await db.orders.delete_many({})
    print(f"   ✅ {orders_deleted.deleted_count} commandes supprimées")
    
    # 4. Remove ALL notifications
    print("🗑️  Suppression de toutes les notifications...")
    notifications_deleted = await db.notifications.delete_many({})
    print(f"   ✅ {notifications_deleted.deleted_count} notifications supprimées")
    
    # 5. Remove ALL chat messages
    print("🗑️  Suppression de tous les messages de chat...")
    chat_deleted = await db.chat_messages.delete_many({})
    print(f"   ✅ {chat_deleted.deleted_count} messages supprimés")
    
    # 6. Clean GridFS files
    print("🗑️  Nettoyage des fichiers GridFS...")
    files_deleted = await db.fs.files.delete_many({})
    chunks_deleted = await db.fs.chunks.delete_many({})
    print(f"   ✅ {files_deleted.deleted_count} fichiers supprimés")
    print(f"   ✅ {chunks_deleted.deleted_count} chunks supprimés")
    
    # 7. Create production admin user
    print("👤 Création de l'utilisateur admin de production...")
    admin_user = {
        "id": str(uuid.uuid4()),
        "email": "admin@dmr-development.com",
        "first_name": "Admin",
        "last_name": "DMR",
        "phone": "0123456789",
        "country": "France",
        "role": "admin",
        "password": hash_password("Admin2024!"),
        "created_at": datetime.utcnow().isoformat()
    }
    
    await db.users.insert_one(admin_user)
    print(f"   ✅ Admin créé: {admin_user['email']}")
    
    # 8. Verify final state
    print("\n📊 État final de la base de données:")
    collections_status = {
        'users': await db.users.count_documents({}),
        'services': await db.services.count_documents({}),
        'orders': await db.orders.count_documents({}),
        'notifications': await db.notifications.count_documents({}),
        'chat_messages': await db.chat_messages.count_documents({}),
        'fs.files': await db.fs.files.count_documents({}),
        'fs.chunks': await db.fs.chunks.count_documents({})
    }
    
    for collection, count in collections_status.items():
        print(f"   - {collection}: {count}")
    
    print(f"\n🎉 Nettoyage final terminé!")
    print(f"📧 Admin: admin@dmr-development.com")
    print(f"🔑 Password: Admin2024!")
    print(f"📝 TOUS les services doivent être créés manuellement via l'interface admin")
    print(f"👥 TOUS les utilisateurs doivent s'inscrire via l'interface client")

async def main():
    await final_cleanup()
    client.close()

if __name__ == "__main__":
    asyncio.run(main())