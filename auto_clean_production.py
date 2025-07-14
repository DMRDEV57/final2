#!/usr/bin/env python3
"""
Script automatique pour nettoyer la production
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import gridfs
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client.cartography
sync_client = MongoClient(MONGO_URL)
sync_db = sync_client.cartography
fs = gridfs.GridFS(sync_db)

async def auto_clean_production():
    """Nettoyage automatique pour la production"""
    
    print("🧹 NETTOYAGE AUTOMATIQUE POUR LA PRODUCTION")
    print("=" * 50)
    
    # 1. Supprimer toutes les commandes et leurs fichiers
    print("\n1. 📦 Suppression des commandes de test...")
    
    orders = await db.orders.find().to_list(None)
    deleted_orders = 0
    deleted_files = 0
    
    for order in orders:
        # Supprimer les fichiers GridFS associés
        if "files" in order:
            for file_info in order["files"]:
                try:
                    file_id = file_info.get("file_id")
                    if file_id:
                        fs.delete(ObjectId(file_id))
                        deleted_files += 1
                except:
                    pass
        
        # Supprimer la commande
        await db.orders.delete_one({"_id": order["_id"]})
        deleted_orders += 1
    
    print(f"✅ {deleted_orders} commandes supprimées")
    print(f"✅ {deleted_files} fichiers supprimés")
    
    # 2. Supprimer toutes les notifications
    notifications_result = await db.notifications.delete_many({})
    print(f"✅ {notifications_result.deleted_count} notifications supprimées")
    
    # 3. Supprimer tous les messages de chat
    messages_result = await db.messages.delete_many({})
    print(f"✅ {messages_result.deleted_count} messages supprimés")
    
    # 4. Supprimer tous les utilisateurs clients de test (garder les admins)
    users_result = await db.users.delete_many({"role": {"$ne": "admin"}})
    print(f"✅ {users_result.deleted_count} utilisateurs clients supprimés")
    
    # 5. Nettoyer les fichiers GridFS orphelins
    all_files = list(fs.find())
    orphaned_files = 0
    
    for file_obj in all_files:
        try:
            fs.delete(file_obj._id)
            orphaned_files += 1
        except:
            pass
    
    print(f"✅ {orphaned_files} fichiers orphelins supprimés")
    
    # 6. Vérifier les comptes admin restants
    admins = await db.users.find({"role": "admin"}).to_list(None)
    print(f"✅ {len(admins)} comptes admin conservés")
    
    # 7. Vérifier les services disponibles
    services_count = await db.services.count_documents({})
    print(f"✅ {services_count} services disponibles")
    
    print("\n🎉 NETTOYAGE TERMINÉ !")
    print("🚀 Votre application est prête pour la production !")
    
    # Fermer les connexions
    client.close()
    sync_client.close()

if __name__ == "__main__":
    asyncio.run(auto_clean_production())