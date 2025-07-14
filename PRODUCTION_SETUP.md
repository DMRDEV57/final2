# DMR DÉVELOPPEMENT - Configuration de Production

## 🚀 Configuration Initiale

L'application DMR DÉVELOPPEMENT est maintenant configurée pour une création manuelle de toutes les données via l'interface utilisateur. Aucune donnée fictive n'est créée automatiquement.

## 🔧 Étapes de Configuration

### 1. Nettoyage des Données Fictives

```bash
cd /app/backend
python clean_mock_data.py
```

Ce script supprime toutes les données de test/fictives existantes :
- Utilisateurs de test
- Services de test
- Commandes de test
- Notifications de test
- Messages de chat de test
- Fichiers associés

### 2. Création d'un Utilisateur Admin

```bash
cd /app/backend
python create_admin.py
```

Ce script interactif permet de créer un utilisateur admin avec :
- Email personnalisé
- Mot de passe sécurisé
- Informations de profil complètes

### 3. Configuration des Services

1. **Connexion Admin** : Se connecter avec les identifiants admin créés
2. **Accès Interface** : Aller dans l'interface d'administration
3. **Créer Services** : Utiliser la section "Services" pour créer :
   - Nom du service
   - Prix
   - Description
   - Statut (actif/inactif)

### 4. Gestion des Utilisateurs

Les nouveaux utilisateurs peuvent :
- **S'inscrire** via l'interface client
- **Être créés** par l'admin via l'interface d'administration

## 📋 Fonctionnalités Disponibles

### Interface Admin
- ✅ Création/modification de services
- ✅ Gestion des utilisateurs
- ✅ Gestion des commandes
- ✅ Upload de fichiers modifiés
- ✅ Notifications temps réel
- ✅ Chat avec les clients

### Interface Client
- ✅ Inscription/connexion
- ✅ Sélection de services
- ✅ Upload de fichiers
- ✅ Suivi des commandes
- ✅ Téléchargement de fichiers modifiés
- ✅ Demandes de SAV
- ✅ Chat avec l'admin

## 🔒 Sécurité

- Tous les mots de passe sont hachés avec bcrypt
- Authentification JWT
- Validation des données avec Pydantic
- Gestion des permissions admin/client

## 📊 Base de Données

### Collections MongoDB
- `users` : Utilisateurs (clients + admin)
- `services` : Services disponibles
- `orders` : Commandes
- `notifications` : Notifications
- `chat_messages` : Messages de chat
- `fs.files` / `fs.chunks` : Fichiers GridFS

### Variables d'Environnement
- `MONGO_URL` : URL de connexion MongoDB
- `MONGO_DB_NAME` : Nom de la base de données
- `JWT_SECRET_KEY` : Clé secrète pour JWT

## 🛠️ Maintenance

### Scripts Utiles
- `create_admin.py` : Créer un utilisateur admin
- `clean_mock_data.py` : Nettoyer les données de test
- `check_db.py` : Vérifier l'état de la base de données

### Redémarrage des Services
```bash
sudo supervisorctl restart all
```

## 📞 Support

Pour toute question ou problème, contactez l'équipe de développement DMR DÉVELOPPEMENT.

---

**Version** : Production Ready  
**Date** : $(date)  
**Statut** : ✅ Prêt pour la production