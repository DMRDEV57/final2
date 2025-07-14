#!/usr/bin/env python3
"""
Script pour changer le mot de passe admin
"""

import asyncio
import os
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def change_admin_password():
    """Change le mot de passe admin"""
    
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
    db = client.cartography
    
    print("🔑 CHANGEMENT MOT DE PASSE ADMIN")
    print("=" * 30)
    
    new_email = input("Nouvel email admin (ou appuyez sur Entrée pour garder admin@test.com): ").strip()
    new_password = input("Nouveau mot de passe admin: ").strip()
    
    if not new_password:
        print("❌ Mot de passe requis")
        return
    
    # Hash du nouveau mot de passe
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    
    # Mise à jour
    update_data = {"password": hashed_password.decode('utf-8')}
    if new_email:
        update_data["email"] = new_email
    
    result = await db.users.update_one(
        {"email": "admin@test.com", "role": "admin"},
        {"$set": update_data}
    )
    
    if result.modified_count > 0:
        print("✅ Mot de passe admin changé avec succès!")
        if new_email:
            print(f"✅ Email changé vers: {new_email}")
    else:
        print("❌ Erreur lors du changement")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(change_admin_password())