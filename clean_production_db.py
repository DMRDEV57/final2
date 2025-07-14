#!/usr/bin/env python3
"""
Script pour nettoyer spécifiquement la base de données de production
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import gridfs
from dotenv import load_dotenv

async def clean_production_database():
    load_dotenv()
    
    # Utiliser la configuration exacte du .env
    MONGO_URL = "mongodb://localhost:27017"
    DB_NAME = "test_database"
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]  # Utiliser explicitement test_database
    
    sync_client = MongoClient(MONGO_URL)
    sync_db = sync_client[DB_NAME]
    fs = gridfs.GridFS(sync_db)
    
    print('🧹 NETTOYAGE DE LA BASE DE DONNÉES PRODUCTION')
    print(f'📊 Base de données: {DB_NAME}')
    print('=' * 50)
    
    # 1. Lister toutes les collections
    collections = await db.list_collection_names()
    print(f'📋 Collections trouvées: {collections}')
    
    # 2. Supprimer toutes les commandes
    if 'orders' in collections:
        # D'abord supprimer les fichiers GridFS
        orders = await db.orders.find().to_list(None)
        deleted_files = 0
        
        for order in orders:
            if "files" in order:
                for file_info in order["files"]:
                    try:
                        file_id = file_info.get("file_id")
                        if file_id:
                            from bson import ObjectId
                            fs.delete(ObjectId(file_id))
                            deleted_files += 1
                    except:
                        pass
        
        # Supprimer toutes les commandes
        orders_result = await db.orders.delete_many({})
        print(f'✅ {orders_result.deleted_count} commandes supprimées')
        print(f'✅ {deleted_files} fichiers supprimés')
    
    # 3. Supprimer toutes les autres collections de données
    collections_to_clean = ['notifications', 'messages']
    
    for collection_name in collections_to_clean:
        if collection_name in collections:
            result = await db[collection_name].delete_many({})
            print(f'✅ {result.deleted_count} {collection_name} supprimées')
    
    # 4. Supprimer tous les utilisateurs non-admin
    if 'users' in collections:
        users_result = await db.users.delete_many({"role": {"$ne": "admin"}})
        print(f'✅ {users_result.deleted_count} utilisateurs clients supprimés')
    
    # 5. Supprimer tous les fichiers GridFS restants
    try:
        all_files = list(fs.find())
        files_deleted = 0
        
        for file_obj in all_files:
            try:
                fs.delete(file_obj._id)
                files_deleted += 1
            except:
                pass
        
        print(f'✅ {files_deleted} fichiers GridFS supprimés')
    except:
        print('⚠️  Pas de fichiers GridFS à supprimer')
    
    # 6. Vérification finale
    print('\n🔍 VÉRIFICATION FINALE:')
    
    remaining_orders = await db.orders.count_documents({})
    remaining_notifications = await db.notifications.count_documents({})
    remaining_messages = await db.messages.count_documents({})
    remaining_users = await db.users.count_documents({"role": {"$ne": "admin"}})
    remaining_files = len(list(fs.find()))
    
    print(f'📦 Commandes restantes: {remaining_orders}')
    print(f'🔔 Notifications restantes: {remaining_notifications}')
    print(f'💬 Messages restants: {remaining_messages}')
    print(f'👥 Utilisateurs clients restants: {remaining_users}')
    print(f'📄 Fichiers GridFS restants: {remaining_files}')
    
    # Vérifier les admins et services
    admin_count = await db.users.count_documents({"role": "admin"})
    services_count = await db.services.count_documents({})
    
    print(f'👑 Admins conservés: {admin_count}')
    print(f'🔧 Services conservés: {services_count}')
    
    print('\n🎉 NETTOYAGE TERMINÉ !')
    
    if remaining_orders == 0 and remaining_notifications == 0 and remaining_messages == 0 and remaining_users == 0 and remaining_files == 0:
        print('✅ BASE DE DONNÉES PRODUCTION PARFAITEMENT NETTOYÉE')
        print('🚀 PRÊTE POUR VOS VRAIS CLIENTS')
    else:
        print('⚠️  Il reste encore des données à nettoyer')
    
    client.close()
    sync_client.close()

if __name__ == "__main__":
    asyncio.run(clean_production_database())