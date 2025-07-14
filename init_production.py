#!/usr/bin/env python3
"""
Script pour initialiser la nouvelle base de données production propre
"""

import asyncio
import os
import bcrypt
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def init_clean_production():
    load_dotenv()
    
    # Utiliser la nouvelle base de données
    MONGO_URL = "mongodb://localhost:27017"
    DB_NAME = "dmr_production"
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print('🚀 INITIALISATION BASE DE DONNÉES PRODUCTION PROPRE')
    print(f'📊 Nouvelle base: {DB_NAME}')
    print('=' * 60)
    
    # Vérifier si la base existe déjà
    collections = await db.list_collection_names()
    if collections:
        print(f'⚠️  Base de données {DB_NAME} existe déjà avec {len(collections)} collections')
        print('🗑️  Suppression pour repartir à zéro...')
        
        for collection_name in collections:
            await db[collection_name].drop()
            print(f'   🗑️  {collection_name} supprimée')
    
    # 1. Créer seulement les 3 services voulus
    print('\n1. 🔧 Création des services production...')
    
    services_production = [
        {
            'id': str(uuid.uuid4()),
            'name': 'Stage 1',
            'price': 150.0,
            'description': 'Optimisation cartographie Stage 1',
            'is_active': True,
            'is_visible': True
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Stage 1 + EGR',
            'price': 200.0,
            'description': 'Stage 1 avec suppression EGR',
            'is_active': True,
            'is_visible': True
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Stage 2',
            'price': 250.0,
            'description': 'Optimisation cartographie Stage 2',
            'is_active': True,
            'is_visible': True
        }
    ]
    
    for service in services_production:
        await db.services.insert_one(service)
        print(f'   ✅ {service["name"]} - {service["price"]}€')
    
    # 2. Créer le compte admin
    print('\n2. 👑 Création du compte admin...')
    
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
    print('   ✅ admin@test.com / admin123')
    
    # 3. Vérification finale
    print('\n3. 📊 Vérification...')
    
    services_count = await db.services.count_documents({})
    users_count = await db.users.count_documents({})
    orders_count = await db.orders.count_documents({})
    
    print(f'   🔧 Services: {services_count}')
    print(f'   👥 Utilisateurs: {users_count}')
    print(f'   📦 Commandes: {orders_count}')
    
    print('\n🎉 BASE DE DONNÉES PRODUCTION INITIALISÉE !')
    print('=' * 60)
    print('✅ Nouvelle base de données complètement propre')
    print('✅ Aucune donnée de test qui peut revenir')
    print('✅ Prête pour redéploiement')
    
    print('\n🚀 PROCHAINES ÉTAPES:')
    print('1. Redéployer l\'application')
    print('2. Tester la connexion admin')
    print('3. Vérifier que les interfaces sont vides')
    print('4. Commencer à recevoir les vrais clients')
    
    client.close()

if __name__ == "__main__":
    asyncio.run(init_clean_production())