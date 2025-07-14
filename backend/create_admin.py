#!/usr/bin/env python3
"""
Script pour créer un utilisateur admin manuellement
Usage: python create_admin.py
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

async def create_admin_user():
    """Create admin user with manual input"""
    print("🔧 DMR DÉVELOPPEMENT - Création d'un utilisateur admin")
    print("=" * 50)
    
    # Check if admin already exists
    admin_exists = await db.users.find_one({"role": "admin"})
    if admin_exists:
        print(f"⚠️  Un utilisateur admin existe déjà: {admin_exists['email']}")
        overwrite = input("Souhaitez-vous créer un nouvel admin quand même? (y/N): ").lower()
        if overwrite != 'y':
            print("❌ Opération annulée")
            return
    
    # Get admin details
    email = input("Email admin: ").strip()
    if not email:
        print("❌ Email requis")
        return
    
    # Check if email already exists
    existing_user = await db.users.find_one({"email": email})
    if existing_user:
        print(f"❌ L'email {email} existe déjà")
        return
    
    password = input("Mot de passe: ").strip()
    if not password:
        print("❌ Mot de passe requis")
        return
    
    first_name = input("Prénom: ").strip() or "Admin"
    last_name = input("Nom: ").strip() or "DMR"
    phone = input("Téléphone: ").strip() or "0000000000"
    country = input("Pays: ").strip() or "France"
    
    # Create admin user
    admin_user = {
        "id": str(uuid.uuid4()),
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "phone": phone,
        "country": country,
        "role": "admin",
        "password": hash_password(password),
        "created_at": datetime.utcnow().isoformat()
    }
    
    try:
        await db.users.insert_one(admin_user)
        print("✅ Utilisateur admin créé avec succès!")
        print(f"📧 Email: {email}")
        print(f"👤 Nom: {first_name} {last_name}")
        print(f"🔑 Mot de passe: {password}")
        print("")
        print("🚀 L'admin peut maintenant se connecter à l'interface d'administration")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'admin: {str(e)}")

async def main():
    await create_admin_user()
    client.close()

if __name__ == "__main__":
    asyncio.run(main())