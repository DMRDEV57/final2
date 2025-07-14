#!/usr/bin/env python3
"""
Script pour créer un utilisateur admin automatiquement
Usage: python create_production_admin.py
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

async def create_production_admin():
    """Create production admin user"""
    print("🔧 DMR DÉVELOPPEMENT - Création d'un utilisateur admin de production")
    print("=" * 60)
    
    # Production admin details
    admin_data = {
        "email": "admin@dmr-development.com",
        "password": "Admin2024!",
        "first_name": "Admin",
        "last_name": "DMR",
        "phone": "0123456789",
        "country": "France"
    }
    
    # Check if admin already exists
    existing_admin = await db.users.find_one({"email": admin_data["email"]})
    if existing_admin:
        print(f"⚠️  Admin existe déjà: {admin_data['email']}")
        return
    
    # Create admin user
    admin_user = {
        "id": str(uuid.uuid4()),
        "email": admin_data["email"],
        "first_name": admin_data["first_name"],
        "last_name": admin_data["last_name"],
        "phone": admin_data["phone"],
        "country": admin_data["country"],
        "role": "admin",
        "password": hash_password(admin_data["password"]),
        "created_at": datetime.utcnow().isoformat()
    }
    
    try:
        await db.users.insert_one(admin_user)
        print("✅ Utilisateur admin de production créé avec succès!")
        print(f"📧 Email: {admin_data['email']}")
        print(f"👤 Nom: {admin_data['first_name']} {admin_data['last_name']}")
        print(f"🔑 Mot de passe: {admin_data['password']}")
        print("")
        print("🚀 L'admin peut maintenant se connecter à l'interface d'administration")
        print("⚠️  IMPORTANT: Changez le mot de passe après la première connexion!")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'admin: {str(e)}")

async def main():
    await create_production_admin()
    client.close()

if __name__ == "__main__":
    asyncio.run(main())