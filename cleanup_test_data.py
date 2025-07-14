#!/usr/bin/env python3
"""
Script de nettoyage des données de test pour DMR DEVELOPPEMENT
À exécuter après le déploiement pour supprimer les données de test
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import gridfs
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client.cartography
sync_client = MongoClient(MONGO_URL)
sync_db = sync_client.cartography
fs = gridfs.GridFS(sync_db)

async def cleanup_test_data():
    """Supprime toutes les données de test en gardant le compte admin principal"""
    
    print("🧹 NETTOYAGE DES DONNÉES DE TEST")
    print("=" * 50)
    
    # 1. Supprimer tous les utilisateurs SAUF l'admin principal
    print("\n1. 👥 Suppression des utilisateurs de test...")
    
    # Garder seulement l'admin principal
    admin_kept = await db.users.find_one({"email": "admin@test.com", "role": "admin"})
    if admin_kept:
        print(f"✅ Compte admin principal conservé: {admin_kept['email']}")
    
    # Supprimer tous les autres utilisateurs
    users_to_delete = await db.users.find({
        "$and": [
            {"role": {"$ne": "admin"}},  # Pas admin
            {"email": {"$ne": "admin@test.com"}}  # Pas l'admin principal
        ]
    }).to_list(None)
    
    deleted_users = 0
    for user in users_to_delete:
        await db.users.delete_one({"_id": user["_id"]})
        deleted_users += 1
        print(f"🗑️  Utilisateur supprimé: {user.get('email', 'email inconnu')}")
    
    print(f"✅ {deleted_users} utilisateurs de test supprimés")
    
    # 2. Supprimer toutes les commandes
    print("\n2. 📦 Suppression des commandes de test...")
    
    # Récupérer toutes les commandes pour supprimer les fichiers associés
    orders = await db.orders.find().to_list(None)
    deleted_orders = 0
    deleted_files = 0
    
    for order in orders:
        # Supprimer les fichiers GridFS associés
        if "files" in order:
            for file_info in order["files"]:
                try:
                    file_id = file_info.get("file_id")
                    if file_id:
                        fs.delete(ObjectId(file_id))
                        deleted_files += 1
                        print(f"🗑️  Fichier supprimé: {file_info.get('filename', 'fichier inconnu')}")
                except Exception as e:
                    print(f"⚠️  Erreur suppression fichier: {e}")
        
        # Supprimer la commande
        await db.orders.delete_one({"_id": order["_id"]})
        deleted_orders += 1
        print(f"🗑️  Commande supprimée: {order.get('order_number', 'ID inconnu')}")
    
    print(f"✅ {deleted_orders} commandes supprimées")
    print(f"✅ {deleted_files} fichiers supprimés")
    
    # 3. Supprimer toutes les notifications
    print("\n3. 🔔 Suppression des notifications de test...")
    
    notifications_count = await db.notifications.count_documents({})
    await db.notifications.delete_many({})
    print(f"✅ {notifications_count} notifications supprimées")
    
    # 4. Supprimer tous les messages de chat
    print("\n4. 💬 Suppression des messages de chat...")
    
    messages_count = await db.messages.count_documents({})
    await db.messages.delete_many({})
    print(f"✅ {messages_count} messages supprimés")
    
    # 5. Garder les services par défaut (optionnel)
    print("\n5. 🔧 Vérification des services...")
    
    services_count = await db.services.count_documents({})
    print(f"ℹ️  {services_count} services conservés (normal)")
    
    # 6. Résumé final
    print("\n" + "=" * 50)
    print("🎉 NETTOYAGE TERMINÉ !")
    print("=" * 50)
    print(f"✅ Compte admin conservé: admin@test.com")
    print(f"✅ {deleted_users} utilisateurs de test supprimés")
    print(f"✅ {deleted_orders} commandes supprimées")
    print(f"✅ {deleted_files} fichiers supprimés")
    print(f"✅ {notifications_count} notifications supprimées")
    print(f"✅ {messages_count} messages supprimés")
    print(f"ℹ️  {services_count} services conservés")
    
    print("\n🚀 Base de données prête pour la production !")
    print("⚠️  N'oubliez pas de changer le mot de passe admin après le nettoyage")

async def show_current_data():
    """Affiche les données actuelles avant nettoyage"""
    
    print("📊 DONNÉES ACTUELLES")
    print("=" * 30)
    
    # Utilisateurs
    users = await db.users.find().to_list(None)
    print(f"👥 Utilisateurs: {len(users)}")
    for user in users:
        print(f"  - {user.get('email', 'email inconnu')} ({user.get('role', 'role inconnu')})")
    
    # Commandes
    orders_count = await db.orders.count_documents({})
    print(f"📦 Commandes: {orders_count}")
    
    # Notifications
    notifications_count = await db.notifications.count_documents({})
    print(f"🔔 Notifications: {notifications_count}")
    
    # Messages
    messages_count = await db.messages.count_documents({})
    print(f"💬 Messages: {messages_count}")
    
    # Services
    services_count = await db.services.count_documents({})
    print(f"🔧 Services: {services_count}")

async def main():
    """Fonction principale"""
    
    print("🗂️  SCRIPT DE NETTOYAGE DMR DEVELOPPEMENT")
    print("=" * 50)
    
    # Afficher les données actuelles
    await show_current_data()
    
    # Demander confirmation
    print("\n⚠️  ATTENTION: Cette action supprimera toutes les données de test!")
    print("✅ Seul le compte admin principal sera conservé")
    
    response = input("\nVoulez-vous continuer ? (oui/non): ").lower()
    
    if response in ['oui', 'o', 'yes', 'y']:
        await cleanup_test_data()
    else:
        print("❌ Nettoyage annulé")
    
    # Fermer les connexions
    client.close()
    sync_client.close()

if __name__ == "__main__":
    asyncio.run(main())