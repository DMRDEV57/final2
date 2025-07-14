#!/usr/bin/env python3
"""
Script de nettoyage RAPIDE - Suppression directe des données de test
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import gridfs
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client.cartography
sync_client = MongoClient(MONGO_URL)
sync_db = sync_client.cartography
fs = gridfs.GridFS(sync_db)

async def quick_cleanup():
    """Nettoyage rapide automatique"""
    
    print("🚀 NETTOYAGE RAPIDE EN COURS...")
    
    # Supprimer tous les utilisateurs sauf admin principal
    result = await db.users.delete_many({
        "$and": [
            {"email": {"$ne": "admin@test.com"}},
            {"role": {"$ne": "admin"}}
        ]
    })
    print(f"✅ {result.deleted_count} utilisateurs de test supprimés")
    
    # Supprimer toutes les commandes et fichiers
    orders = await db.orders.find().to_list(None)
    files_deleted = 0
    
    for order in orders:
        if "files" in order:
            for file_info in order["files"]:
                try:
                    file_id = file_info.get("file_id")
                    if file_id:
                        fs.delete(ObjectId(file_id))
                        files_deleted += 1
                except:
                    pass
    
    orders_result = await db.orders.delete_many({})
    print(f"✅ {orders_result.deleted_count} commandes supprimées")
    print(f"✅ {files_deleted} fichiers supprimés")
    
    # Supprimer notifications et messages
    notif_result = await db.notifications.delete_many({})
    msg_result = await db.messages.delete_many({})
    
    print(f"✅ {notif_result.deleted_count} notifications supprimées")
    print(f"✅ {msg_result.deleted_count} messages supprimés")
    
    print("\n🎉 NETTOYAGE TERMINÉ !")
    print("🔑 Compte admin conservé: admin@test.com")
    print("⚠️  Changez le mot de passe admin maintenant !")
    
    client.close()
    sync_client.close()

if __name__ == "__main__":
    asyncio.run(quick_cleanup())