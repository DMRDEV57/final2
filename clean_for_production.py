#!/usr/bin/env python3
"""
Script pour supprimer toutes les commandes de test et préparer la production
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import gridfs
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client.cartography
sync_client = MongoClient(MONGO_URL)
sync_db = sync_client.cartography
fs = gridfs.GridFS(sync_db)

async def clean_production_data():
    """Supprime toutes les commandes de test et prépare la production"""
    
    print("🧹 NETTOYAGE POUR LA PRODUCTION")
    print("=" * 50)
    
    # 1. Supprimer toutes les commandes et leurs fichiers
    print("\n1. 📦 Suppression des commandes de test...")
    
    orders = await db.orders.find().to_list(None)
    deleted_orders = 0
    deleted_files = 0
    
    for order in orders:
        print(f"🗑️  Suppression commande: {order.get('order_number', 'ID inconnu')}")
        
        # Supprimer les fichiers GridFS associés
        if "files" in order:
            for file_info in order["files"]:
                try:
                    file_id = file_info.get("file_id")
                    if file_id:
                        fs.delete(ObjectId(file_id))
                        deleted_files += 1
                        print(f"   📄 Fichier supprimé: {file_info.get('filename', 'fichier inconnu')}")
                except Exception as e:
                    print(f"   ⚠️  Erreur suppression fichier: {e}")
        
        # Supprimer la commande
        await db.orders.delete_one({"_id": order["_id"]})
        deleted_orders += 1
    
    print(f"✅ {deleted_orders} commandes supprimées")
    print(f"✅ {deleted_files} fichiers supprimés")
    
    # 2. Supprimer toutes les notifications
    print("\n2. 🔔 Suppression des notifications...")
    
    notifications_result = await db.notifications.delete_many({})
    print(f"✅ {notifications_result.deleted_count} notifications supprimées")
    
    # 3. Supprimer tous les messages de chat
    print("\n3. 💬 Suppression des messages de chat...")
    
    messages_result = await db.messages.delete_many({})
    print(f"✅ {messages_result.deleted_count} messages supprimés")
    
    # 4. Supprimer tous les utilisateurs clients de test (garder les admins)
    print("\n4. 👥 Suppression des utilisateurs clients de test...")
    
    # Supprimer tous les utilisateurs qui ne sont pas admin
    users_result = await db.users.delete_many({"role": {"$ne": "admin"}})
    print(f"✅ {users_result.deleted_count} utilisateurs clients supprimés")
    
    # 5. Nettoyer les fichiers GridFS orphelins
    print("\n5. 🧹 Nettoyage des fichiers orphelins...")
    
    # Obtenir tous les fichiers GridFS
    all_files = list(fs.find())
    orphaned_files = 0
    
    for file_obj in all_files:
        try:
            # Vérifier si le fichier est référencé dans une commande
            file_id_str = str(file_obj._id)
            order_with_file = await db.orders.find_one({"files.file_id": file_id_str})
            
            if not order_with_file:
                # Fichier orphelin, le supprimer
                fs.delete(file_obj._id)
                orphaned_files += 1
                print(f"   🗑️  Fichier orphelin supprimé: {file_obj.filename}")
        except Exception as e:
            print(f"   ⚠️  Erreur nettoyage fichier: {e}")
    
    print(f"✅ {orphaned_files} fichiers orphelins supprimés")
    
    # 6. Vérifier les comptes admin restants
    print("\n6. 🔑 Vérification des comptes admin...")
    
    admins = await db.users.find({"role": "admin"}).to_list(None)
    print(f"✅ {len(admins)} comptes admin conservés:")
    for admin in admins:
        print(f"   - {admin.get('email')} ({admin.get('first_name', 'Nom inconnu')})")
    
    # 7. Vérifier les services disponibles
    print("\n7. 🔧 Vérification des services...")
    
    services_count = await db.services.count_documents({})
    print(f"✅ {services_count} services disponibles")
    
    # 8. Résumé final
    print("\n" + "=" * 50)
    print("🎉 NETTOYAGE PRODUCTION TERMINÉ !")
    print("=" * 50)
    print(f"✅ {deleted_orders} commandes de test supprimées")
    print(f"✅ {deleted_files} fichiers supprimés")
    print(f"✅ {notifications_result.deleted_count} notifications supprimées")
    print(f"✅ {messages_result.deleted_count} messages supprimés")
    print(f"✅ {users_result.deleted_count} clients de test supprimés")
    print(f"✅ {orphaned_files} fichiers orphelins supprimés")
    print(f"✅ {len(admins)} comptes admin conservés")
    print(f"✅ {services_count} services disponibles")
    
    print("\n🚀 VOTRE APPLICATION EST PRÊTE POUR LA PRODUCTION !")
    print("💡 Vous pouvez maintenant:")
    print("   - Recevoir de vrais clients")
    print("   - Traiter de vraies commandes")
    print("   - Commencer votre activité")
    
    # Fermer les connexions
    client.close()
    sync_client.close()

async def show_current_data():
    """Affiche les données actuelles avant nettoyage"""
    
    print("📊 DONNÉES ACTUELLES À SUPPRIMER")
    print("=" * 40)
    
    # Commandes
    orders_count = await db.orders.count_documents({})
    print(f"📦 Commandes: {orders_count}")
    
    # Fichiers
    files_count = len(list(fs.find()))
    print(f"📄 Fichiers: {files_count}")
    
    # Notifications
    notifications_count = await db.notifications.count_documents({})
    print(f"🔔 Notifications: {notifications_count}")
    
    # Messages
    messages_count = await db.messages.count_documents({})
    print(f"💬 Messages: {messages_count}")
    
    # Utilisateurs
    users = await db.users.find().to_list(None)
    admins = [u for u in users if u.get('role') == 'admin']
    clients = [u for u in users if u.get('role') != 'admin']
    
    print(f"👥 Utilisateurs: {len(users)} (Admin: {len(admins)}, Clients: {len(clients)})")
    
    # Services
    services_count = await db.services.count_documents({})
    print(f"🔧 Services: {services_count}")

async def main():
    """Fonction principale"""
    
    print("🗂️  NETTOYAGE PRODUCTION - DMR DEVELOPPEMENT")
    print("=" * 60)
    
    # Afficher les données actuelles
    await show_current_data()
    
    # Demander confirmation
    print("\n⚠️  ATTENTION: Cette action supprimera toutes les données de test!")
    print("✅ Seuls les comptes admin et services seront conservés")
    print("🚀 Votre application sera prête pour la production")
    
    response = input("\nVoulez-vous continuer ? (oui/non): ").lower()
    
    if response in ['oui', 'o', 'yes', 'y']:
        await clean_production_data()
    else:
        print("❌ Nettoyage annulé")
        client.close()
        sync_client.close()

if __name__ == "__main__":
    asyncio.run(main())