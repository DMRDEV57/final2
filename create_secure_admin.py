#!/usr/bin/env python3
"""
Script pour créer un compte admin sécurisé en production
"""

import asyncio
import os
import bcrypt
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def create_secure_admin():
    """Crée un compte admin sécurisé"""
    
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
    db = client.cartography
    
    print("🔑 CRÉATION COMPTE ADMIN SÉCURISÉ")
    print("=" * 40)
    
    # Identifiants sécurisés
    email = "dmr.dev57@gmail.com"
    password = "AdminDMR2024-@"
    
    print(f"📧 Email : {email}")
    print(f"🔒 Mot de passe : {'*' * len(password)}")
    
    # Vérifier si l'admin existe déjà
    existing_admin = await db.users.find_one({"email": email})
    
    if existing_admin:
        print("⚠️  Compte admin existe déjà, mise à jour...")
        
        # Mettre à jour le mot de passe
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        result = await db.users.update_one(
            {"email": email},
            {"$set": {"password": hashed_password.decode('utf-8')}}
        )
        
        if result.modified_count > 0:
            print("✅ Mot de passe admin mis à jour")
        
    else:
        print("🆕 Création nouveau compte admin...")
        
        # Hasher le mot de passe
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Créer le compte admin
        admin_user = {
            "id": str(uuid.uuid4()),
            "email": email,
            "password": hashed_password.decode('utf-8'),
            "first_name": "Admin",
            "last_name": "DMR",
            "role": "admin",
            "is_active": True,
            "phone": "0000000000",
            "country": "France",
            "discount_percentage": 0,
            "created_at": "2024-01-01T00:00:00"
        }
        
        await db.users.insert_one(admin_user)
        print("✅ Compte admin créé avec succès")
    
    # Vérifier les autres comptes admin de test
    test_admins = await db.users.find({"email": "admin@test.com"}).to_list(None)
    for admin in test_admins:
        await db.users.delete_one({"_id": admin["_id"]})
        print("🗑️  Ancien compte admin@test.com supprimé")
    
    # Créer des services par défaut si pas encore créés
    services_count = await db.services.count_documents({})
    
    if services_count == 0:
        print("🔧 Création des services par défaut...")
        
        default_services = [
            {
                "id": str(uuid.uuid4()),
                "name": "Stage 1",
                "description": "Optimisation cartographie Stage 1",
                "price": 150,
                "is_active": True,
                "is_visible": True
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Stage 1 + EGR",
                "description": "Stage 1 avec suppression EGR",
                "price": 200,
                "is_active": True,
                "is_visible": True
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Stage 2",
                "description": "Optimisation cartographie Stage 2",
                "price": 250,
                "is_active": True,
                "is_visible": True
            }
        ]
        
        for service in default_services:
            await db.services.insert_one(service)
        
        print(f"✅ {len(default_services)} services créés")
    
    print("\n🎉 CONFIGURATION TERMINÉE !")
    print("=" * 40)
    print("🔐 IDENTIFIANTS DE CONNEXION ADMIN :")
    print(f"📧 Email : {email}")
    print(f"🔒 Mot de passe : {password}")
    print("\n⚠️  IMPORTANT :")
    print("- Notez ces identifiants en lieu sûr")
    print("- Testez la connexion sur votre site déployé")
    print("- Application prête pour la production")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_secure_admin())