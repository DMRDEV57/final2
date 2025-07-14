#!/usr/bin/env python3
"""
Nettoyage de la VRAIE base de données de production
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import gridfs
from dotenv import load_dotenv
import bcrypt
import uuid

async def clean_real_production_db():
    load_dotenv()
    
    # Utiliser les VRAIES variables d'environnement
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'dmr_production')
    
    print("🔧 NETTOYAGE DE LA VRAIE BASE DE DONNÉES DE PRODUCTION")
    print(f"🌐 MongoDB URL: {mongo_url}")
    print(f"📊 Database: {db_name}")
    print("=" * 60)
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    sync_client = MongoClient(mongo_url)
    sync_db = sync_client[db_name]
    fs = gridfs.GridFS(sync_db)
    
    # 1. Supprimer toutes les collections
    collections = await db.list_collection_names()
    print(f"📋 Collections trouvées: {collections}")
    
    for collection_name in collections:
        if not collection_name.startswith('system'):
            await db[collection_name].drop()
            print(f"🗑️  Collection {collection_name} supprimée")
    
    # 2. Créer seulement les 3 services voulus
    print("\n🔧 Création des 3 services de production...")
    
    services = [
        {
            "id": str(uuid.uuid4()),
            "name": "Stage 1",
            "price": 150.0,
            "description": "Optimisation cartographie Stage 1",
            "is_active": True,
            "is_visible": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Stage 1 + EGR",
            "price": 200.0,
            "description": "Stage 1 avec suppression EGR",
            "is_active": True,
            "is_visible": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Stage 2",
            "price": 250.0,
            "description": "Optimisation cartographie Stage 2",
            "is_active": True,
            "is_visible": True
        }
    ]
    
    for service in services:
        await db.services.insert_one(service)
        print(f"✅ Service: {service['name']} - {service['price']}€")
    
    # 3. Créer compte admin
    print("\n👑 Création du compte admin...")
    
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
    print("✅ Compte admin créé: admin@test.com / admin123")
    
    # 4. Vérification finale
    print("\n📊 VÉRIFICATION FINALE:")
    
    services_count = await db.services.count_documents({})
    users_count = await db.users.count_documents({})
    orders_count = await db.orders.count_documents({})
    
    print(f"🔧 Services: {services_count}")
    print(f"👥 Utilisateurs: {users_count}")
    print(f"📦 Commandes: {orders_count}")
    
    if services_count == 3 and users_count == 1 and orders_count == 0:
        print("\n🎉 PARFAIT ! BASE DE DONNÉES DE PRODUCTION NETTOYÉE !")
        print("✅ 3 services seulement")
        print("✅ 1 admin seulement")
        print("✅ 0 commandes")
        print("🚀 Prête pour redéploiement")
    else:
        print("\n⚠️  Problème détecté dans le nettoyage")
    
    client.close()
    sync_client.close()

if __name__ == "__main__":
    asyncio.run(clean_real_production_db())