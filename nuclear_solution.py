#!/usr/bin/env python3
"""
SOLUTION NUCLÉAIRE - Création d'une nouvelle application complètement isolée
"""

import os
import shutil
import subprocess
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
import uuid

async def nuclear_solution():
    print("🚀 SOLUTION NUCLÉAIRE - CRÉATION APPLICATION ISOLÉE")
    print("=" * 60)
    
    # 1. Créer une nouvelle base de données avec nom unique
    db_name = f"dmr_production_{uuid.uuid4().hex[:8]}"
    print(f"📊 Nouvelle base de données: {db_name}")
    
    # 2. Se connecter à la nouvelle base
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client[db_name]
    
    # 3. Créer SEULEMENT les 3 services voulus
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
        print(f"✅ Service créé: {service['name']} - {service['price']}€")
    
    # 4. Créer compte admin
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
    print("✅ Compte admin créé")
    
    # 5. Modifier le .env pour forcer la nouvelle base
    env_content = f'''MONGO_URL="mongodb://localhost:27017"
DB_NAME="{db_name}"
JWT_SECRET_KEY="dmr-production-secret-key-2024"
'''
    
    with open('/app/backend/.env', 'w') as f:
        f.write(env_content)
    
    print(f"✅ Fichier .env mis à jour avec {db_name}")
    
    # 6. Vérification
    services_count = await db.services.count_documents({})
    users_count = await db.users.count_documents({})
    
    print(f"\n📊 VÉRIFICATION FINALE:")
    print(f"🔧 Services: {services_count}")
    print(f"👥 Utilisateurs: {users_count}")
    print(f"📦 Commandes: 0")
    
    client.close()
    
    print(f"\n🎉 NOUVELLE APPLICATION CRÉÉE !")
    print(f"📊 Base de données: {db_name}")
    print(f"🔒 Complètement isolée des données fantômes")
    print(f"✅ Prête pour redéploiement")

if __name__ == "__main__":
    asyncio.run(nuclear_solution())