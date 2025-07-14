#!/usr/bin/env python3
"""
Script de diagnostic et correction du problème de connexion admin
"""

import asyncio
import os
import bcrypt
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def diagnose_and_fix_login():
    load_dotenv()
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
    db = client.cartography
    
    print("🔍 DIAGNOSTIC DU PROBLÈME DE CONNEXION")
    print("=" * 50)
    
    # 1. Vérifier l'utilisateur admin
    admin_email = "dmr.dev57@gmail.com"
    admin_password = "AdminDMR2024-@"
    
    print(f"📧 Recherche de l'utilisateur: {admin_email}")
    
    admin_user = await db.users.find_one({"email": admin_email})
    
    if not admin_user:
        print("❌ Utilisateur admin non trouvé")
        print("🔧 Création d'un nouvel utilisateur admin...")
        
        # Créer un nouvel admin
        hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
        
        new_admin = {
            "id": str(uuid.uuid4()),
            "email": admin_email,
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
        
        await db.users.insert_one(new_admin)
        print("✅ Nouvel utilisateur admin créé")
        
    else:
        print("✅ Utilisateur admin trouvé")
        print(f"🔑 Role: {admin_user.get('role')}")
        print(f"📊 Actif: {admin_user.get('is_active')}")
        print(f"🆔 ID: {admin_user.get('id')}")
        
        # Vérifier le mot de passe
        stored_password = admin_user.get('password')
        if stored_password:
            try:
                # Tester la vérification du mot de passe
                password_valid = bcrypt.checkpw(admin_password.encode('utf-8'), stored_password.encode('utf-8'))
                print(f"🔒 Mot de passe valide: {password_valid}")
                
                if not password_valid:
                    print("🔧 Réinitialisation du mot de passe...")
                    # Réinitialiser le mot de passe
                    new_hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
                    
                    result = await db.users.update_one(
                        {"email": admin_email},
                        {"$set": {"password": new_hashed_password.decode('utf-8'), "is_active": True}}
                    )
                    
                    if result.modified_count > 0:
                        print("✅ Mot de passe réinitialisé avec succès")
                    else:
                        print("❌ Erreur lors de la réinitialisation")
                
            except Exception as e:
                print(f"❌ Erreur lors de la vérification du mot de passe: {e}")
                print("🔧 Création d'un nouveau hash...")
                
                # Créer un nouveau hash
                new_hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
                
                result = await db.users.update_one(
                    {"email": admin_email},
                    {"$set": {"password": new_hashed_password.decode('utf-8'), "is_active": True}}
                )
                
                if result.modified_count > 0:
                    print("✅ Nouveau hash créé avec succès")
        
        else:
            print("❌ Pas de mot de passe stocké")
            print("🔧 Ajout du mot de passe...")
            
            hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
            
            result = await db.users.update_one(
                {"email": admin_email},
                {"$set": {"password": hashed_password.decode('utf-8'), "is_active": True}}
            )
            
            if result.modified_count > 0:
                print("✅ Mot de passe ajouté avec succès")
    
    # 2. Créer un compte simple pour test
    simple_email = "admin@test.com"
    simple_password = "admin123"
    
    print(f"\n🔧 Création d'un compte de test simple: {simple_email}")
    
    # Supprimer s'il existe déjà
    await db.users.delete_many({"email": simple_email})
    
    # Créer le compte simple
    simple_hashed = bcrypt.hashpw(simple_password.encode('utf-8'), bcrypt.gensalt())
    
    simple_admin = {
        "id": str(uuid.uuid4()),
        "email": simple_email,
        "password": simple_hashed.decode('utf-8'),
        "first_name": "Admin",
        "last_name": "Test",
        "role": "admin",
        "is_active": True,
        "phone": "0000000000",
        "country": "France",
        "discount_percentage": 0,
        "created_at": "2024-01-01T00:00:00"
    }
    
    await db.users.insert_one(simple_admin)
    print("✅ Compte de test simple créé")
    
    # 3. Résumé final
    print("\n" + "=" * 50)
    print("🎉 DIAGNOSTIC ET CORRECTION TERMINÉS")
    print("=" * 50)
    
    print("🔐 COMPTES DISPONIBLES POUR CONNEXION:")
    print(f"1. 📧 {admin_email}")
    print(f"   🔒 {admin_password}")
    print(f"2. 📧 {simple_email}")
    print(f"   🔒 {simple_password}")
    
    print("\n⚠️  TESTEZ MAINTENANT:")
    print("1. Rafraîchissez la page de connexion")
    print("2. Essayez de vous connecter avec l'un des comptes")
    print("3. Si le problème persiste, il y a un problème avec l'API")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(diagnose_and_fix_login())