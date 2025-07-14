#!/usr/bin/env python3
"""
Vérification détaillée de la base de données
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import gridfs
from dotenv import load_dotenv

async def check_real_data():
    load_dotenv()
    MONGO_URL = os.environ.get('MONGO_URL')
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.cartography
    sync_client = MongoClient(MONGO_URL)
    sync_db = sync_client.cartography
    fs = gridfs.GridFS(sync_db)
    
    print('📊 VÉRIFICATION RÉELLE DE LA BASE DE DONNÉES')
    print('=' * 50)
    
    # Commandes
    orders = await db.orders.find().to_list(None)
    print(f'📦 Commandes: {len(orders)}')
    for order in orders:
        print(f'  - {order.get("order_number", "ID inconnu")} - {order.get("status", "statut inconnu")} - Client: {order.get("user_id", "user inconnu")}')
    
    # Utilisateurs
    users = await db.users.find().to_list(None)
    print(f'👥 Utilisateurs: {len(users)}')
    for user in users:
        print(f'  - {user.get("email", "email inconnu")} ({user.get("role", "role inconnu")})')
    
    # Fichiers GridFS
    files = list(fs.find())
    print(f'📄 Fichiers GridFS: {len(files)}')
    for file in files:
        print(f'  - {file.filename} ({file._id})')
    
    # Notifications
    notifications = await db.notifications.find().to_list(None)
    print(f'🔔 Notifications: {len(notifications)}')
    
    # Messages
    messages = await db.messages.find().to_list(None)
    print(f'💬 Messages: {len(messages)}')
    
    # Services
    services = await db.services.find().to_list(None)
    print(f'🔧 Services: {len(services)}')
    for service in services:
        print(f'  - {service.get("name", "nom inconnu")} - {service.get("price", "prix inconnu")}€')
    
    client.close()
    sync_client.close()

if __name__ == "__main__":
    asyncio.run(check_real_data())