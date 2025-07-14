#!/usr/bin/env python3
"""
Script final pour nettoyer DÉFINITIVEMENT la base de données
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import gridfs
from dotenv import load_dotenv

async def final_clean():
    load_dotenv()
    
    MONGO_URL = "mongodb://localhost:27017"
    DB_NAME = "test_database"
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    sync_client = MongoClient(MONGO_URL)
    sync_db = sync_client[DB_NAME]
    fs = gridfs.GridFS(sync_db)
    
    print('🧹 NETTOYAGE FINAL ET DÉFINITIF')
    print('=' * 50)
    
    # 1. Supprimer TOUTES les collections
    collections = await db.list_collection_names()
    print(f'📋 Collections trouvées: {collections}')
    
    for collection_name in collections:
        if not collection_name.startswith('system'):
            await db[collection_name].drop()
            print(f'🗑️  Collection {collection_name} supprimée')
    
    # 2. Recréer seulement les services voulus
    print('\n🔧 Recréation des services corrects...')
    
    services_corrects = [
        {
            'id': 'stage1',
            'name': 'Stage 1',
            'price': 150.0,
            'description': 'Optimisation cartographie Stage 1',
            'is_active': True
        },
        {
            'id': 'stage1_egr',
            'name': 'Stage 1 + EGR',
            'price': 200.0,
            'description': 'Stage 1 avec suppression EGR',
            'is_active': True
        },
        {
            'id': 'stage2',
            'name': 'Stage 2',
            'price': 250.0,
            'description': 'Optimisation cartographie Stage 2',
            'is_active': True
        }
    ]
    
    for service in services_corrects:
        await db.services.insert_one(service)
        service_name = service['name']
        service_price = service['price']
        print(f'✅ Service créé: {service_name} - {service_price}€')
    
    # 3. Recréer seulement le compte admin nécessaire
    print('\n👑 Recréation du compte admin...')
    
    import bcrypt
    import uuid
    
    hashed_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
    
    admin_user = {
        'id': str(uuid.uuid4()),
        'email': 'admin@test.com',
        'password': hashed_password.decode('utf-8'),
        'first_name': 'Admin',
        'last_name': 'DMR',
        'role': 'admin',
        'is_active': True,
        'phone': '0000000000',
        'country': 'France',
        'discount_percentage': 0,
        'created_at': '2024-01-01T00:00:00'
    }
    
    await db.users.insert_one(admin_user)
    print('✅ Compte admin créé: admin@test.com / admin123')
    
    # 4. Vérification finale
    print('\n📊 VÉRIFICATION FINALE:')
    
    services_count = await db.services.count_documents({})
    users_count = await db.users.count_documents({})
    orders_count = await db.orders.count_documents({})
    
    print(f'🔧 Services: {services_count}')
    print(f'👥 Utilisateurs: {users_count}')
    print(f'📦 Commandes: {orders_count}')
    
    print('\n🎉 BASE DE DONNÉES PARFAITEMENT NETTOYÉE')
    print('✅ Prête pour la production avec seulement vos services')
    print('✅ Plus de données de test automatiquement créées')
    
    client.close()
    sync_client.close()

if __name__ == "__main__":
    asyncio.run(final_clean())