#!/usr/bin/env python3
"""
Script de nettoyage complet et forcé pour la production
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import gridfs
from bson import ObjectId
from dotenv import load_dotenv

async def force_clean_all():
    load_dotenv()
    MONGO_URL = os.environ.get('MONGO_URL')
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.cartography
    sync_client = MongoClient(MONGO_URL)
    sync_db = sync_client.cartography
    fs = gridfs.GridFS(sync_db)
    
    print('🧹 NETTOYAGE COMPLET ET FORCÉ')
    print('=' * 50)
    
    # 1. Forcer la suppression de TOUTES les commandes
    print('\n1. 🗑️  Suppression FORCÉE de toutes les commandes...')
    
    # Obtenir toutes les commandes avec tous les champs possibles
    all_orders = await db.orders.find({}).to_list(None)
    print(f'   📦 {len(all_orders)} commandes trouvées')
    
    # Supprimer tous les fichiers référencés
    total_files_deleted = 0
    for order in all_orders:
        print(f'   🗑️  Suppression commande: {order.get("order_number", order.get("id", "inconnu"))}')
        
        # Supprimer tous les fichiers associés
        if "files" in order:
            for file_info in order["files"]:
                file_id = file_info.get("file_id")
                if file_id:
                    try:
                        fs.delete(ObjectId(file_id))
                        total_files_deleted += 1
                    except:
                        pass
    
    # Supprimer toutes les commandes d'un coup
    delete_orders_result = await db.orders.delete_many({})
    print(f'   ✅ {delete_orders_result.deleted_count} commandes supprimées')
    print(f'   ✅ {total_files_deleted} fichiers supprimés')
    
    # 2. Supprimer tous les fichiers GridFS restants
    print('\n2. 🗑️  Suppression de tous les fichiers GridFS...')
    
    all_files = list(fs.find())
    files_deleted = 0
    
    for file_obj in all_files:
        try:
            fs.delete(file_obj._id)
            files_deleted += 1
        except:
            pass
    
    print(f'   ✅ {files_deleted} fichiers GridFS supprimés')
    
    # 3. Nettoyer toutes les collections
    print('\n3. 🧹 Nettoyage des autres collections...')
    
    # Notifications
    notif_result = await db.notifications.delete_many({})
    print(f'   ✅ {notif_result.deleted_count} notifications supprimées')
    
    # Messages
    msg_result = await db.messages.delete_many({})
    print(f'   ✅ {msg_result.deleted_count} messages supprimés')
    
    # Utilisateurs non-admin
    users_result = await db.users.delete_many({"role": {"$ne": "admin"}})
    print(f'   ✅ {users_result.deleted_count} utilisateurs clients supprimés')
    
    # 4. Vérification finale
    print('\n4. 🔍 Vérification finale...')
    
    # Vérifier qu'il n'y a plus de commandes
    remaining_orders = await db.orders.count_documents({})
    print(f'   📦 Commandes restantes: {remaining_orders}')
    
    # Vérifier qu'il n'y a plus de fichiers
    remaining_files = len(list(fs.find()))
    print(f'   📄 Fichiers restants: {remaining_files}')
    
    # Vérifier les admins
    admins = await db.users.find({"role": "admin"}).to_list(None)
    print(f'   👥 Admins conservés: {len(admins)}')
    
    # Vérifier les services
    services_count = await db.services.count_documents({})
    print(f'   🔧 Services disponibles: {services_count}')
    
    # 5. Résumé final
    print('\n' + '=' * 50)
    print('🎉 NETTOYAGE COMPLET TERMINÉ !')
    print('=' * 50)
    
    if remaining_orders == 0 and remaining_files == 0:
        print('✅ BASE DE DONNÉES PARFAITEMENT NETTOYÉE')
        print('🚀 VOTRE APPLICATION EST PRÊTE POUR LA PRODUCTION')
    else:
        print('⚠️  Il reste encore des données')
        print(f'   📦 Commandes: {remaining_orders}')
        print(f'   📄 Fichiers: {remaining_files}')
    
    client.close()
    sync_client.close()

if __name__ == "__main__":
    asyncio.run(force_clean_all())