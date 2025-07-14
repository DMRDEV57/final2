#!/usr/bin/env python3
"""
Script pour changer le mot de passe et email admin - Version directe
"""

import asyncio
import os
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def update_admin_credentials():
    """Met à jour les identifiants admin"""
    
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
    db = client.cartography
    
    print("🔑 MISE À JOUR DES IDENTIFIANTS ADMIN")
    print("=" * 40)
    
    # Nouveaux identifiants
    new_email = "dmr.dev57@gmail.com"
    new_password = "AdminDMR2024-@"
    
    print(f"📧 Nouvel email : {new_email}")
    print(f"🔒 Nouveau mot de passe : {'*' * len(new_password)}")
    
    # Hash du nouveau mot de passe
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    
    # Vérifier si l'admin existe
    admin_user = await db.users.find_one({"email": "admin@test.com", "role": "admin"})
    
    if not admin_user:
        print("❌ Utilisateur admin non trouvé")
        client.close()
        return
    
    print(f"✅ Utilisateur admin trouvé : {admin_user.get('first_name', 'Admin')}")
    
    # Mise à jour des identifiants
    update_data = {
        "email": new_email,
        "password": hashed_password.decode('utf-8')
    }
    
    result = await db.users.update_one(
        {"email": "admin@test.com", "role": "admin"},
        {"$set": update_data}
    )
    
    if result.modified_count > 0:
        print("\n🎉 MISE À JOUR RÉUSSIE !")
        print("=" * 40)
        print(f"✅ Email changé vers : {new_email}")
        print(f"✅ Mot de passe sécurisé mis à jour")
        print(f"✅ Compte admin sécurisé pour la production")
        
        print("\n🔐 NOUVEAUX IDENTIFIANTS DE CONNEXION :")
        print(f"📧 Email : {new_email}")
        print(f"🔒 Mot de passe : {new_password}")
        
        print("\n⚠️  IMPORTANT :")
        print("- Notez ces identifiants en lieu sûr")
        print("- Testez la connexion sur votre site")
        print("- L'ancien compte admin@test.com est désactivé")
        
    else:
        print("❌ Erreur lors de la mise à jour")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(update_admin_credentials())