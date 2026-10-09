# Plateforme Anti-Arnaque

Application web de signalement et de consultation d’arnaques en ligne, avec une interface React côté client et une API Django REST côté serveur.

## Sommaire
- [Objectif du projet](#objectif-du-projet)
- [Fonctionnalités disponibles](#fonctionnalités-disponibles)
- [Stack technique](#stack-technique)
- [Organisation du dépôt](#organisation-du-dépôt)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration (variables d’environnement)](#configuration-variables-denvironnement)
- [Lancement en développement](#lancement-en-développement)
- [Tests et qualité](#tests-et-qualité)
- [Build](#build)
- [Déploiement (éléments présents dans le dépôt)](#déploiement-éléments-présents-dans-le-dépôt)
- [API backend (aperçu)](#api-backend-aperçu)
- [Contribution](#contribution)

## Objectif du projet
La plateforme permet de :
- signaler une arnaque (avec informations de contact et preuves),
- consulter des signalements publiés,
- rechercher un numéro/profil vendeur,
- voter et commenter pour enrichir la fiabilité communautaire,
- gérer un compte utilisateur,
- interagir avec un assistant de support (chatbot à base de FAQ/mots-clés).

## Fonctionnalités disponibles
Basé sur le code actuel du dépôt (`frontend/src` et `backend/*`) :

- **Authentification** : inscription, connexion, déconnexion, profil utilisateur (`/api/auth/*`).
- **Signalements** : création, listing, détail, recherche, stats, types d’arnaque (`/api/signalements/*`).
- **Preuves** : upload de fichiers via endpoint dédié (`/api/signalements/upload/`).
- **Interactions communautaires** : votes (`/api/votes/`) et commentaires (`/api/commentaires/`).
- **Administration/API de dashboard** : endpoints dédiés dans `backend/administration`.
- **Chatbot** : endpoint `POST /api/chat/` (réponses FAQ par matching de mots-clés).
- **Module IA côté backend** : chargement d’un modèle/joblib dans l’app `signalements`.

> Note : le dépôt contient aussi des vues Django « template » dans `backend/signalements/views.py` (tableau de bord, alertes, clusters, dossiers, PDF, etc.). L’interface React actuelle consomme principalement les routes API DRF.

## Stack technique
- **Frontend** : React, Vite, React Router, Axios
- **Backend** : Django, Django REST Framework, django-cors-headers
- **Base de données** : PostgreSQL (configuration via variables `DB_*`)
- **Stockage de preuves** : Azure Blob Storage (variables `AZURE_*`)
- **ML/Data** : scikit-learn, joblib, numpy/scipy (côté backend)

## Organisation du dépôt
```text
.
├── backend/
│   ├── config/                # settings, urls, wsgi/asgi
│   ├── users/                 # auth + profil
│   ├── signalements/          # coeur métier + upload + ML + commandes
│   ├── commentaire/           # commentaires
│   ├── votes/                 # votes
│   ├── administration/        # endpoints admin/dashboard
│   ├── chatbot/               # assistant FAQ
│   ├── .env.example
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/             # Home, Login, Register, Profile, Signalements...
│   │   ├── components/        # Chatbot
│   │   └── services/api.js    # client Axios + CSRF
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## Prérequis
- Python 3 (version compatible avec Django 5.2)
- Node.js + npm (version LTS recommandée)
- Une base PostgreSQL accessible
- Un compte/config Azure Blob Storage si vous utilisez l’upload de preuves

## Installation
Depuis la racine du dépôt.

### 1) Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Frontend
```bash
cd frontend
npm install
```

## Configuration (variables d’environnement)
Le backend charge les variables depuis `backend/.env` (voir `backend/.env.example`).

```bash
cd backend
cp .env.example .env
```

Variables présentes dans l’exemple :
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `AZURE_STORAGE_CONNECTION_STRING`
- `AZURE_ACCOUNT_NAME`
- `AZURE_CONTAINER_NAME`

> Important : remplacez toutes les valeurs de démonstration par vos propres secrets avant un usage réel.

## Lancement en développement
Le frontend Vite est configuré pour proxy `/api` vers `http://127.0.0.1:8000` (`frontend/vite.config.js`).

### 1) Démarrer le backend
```bash
cd backend
source .venv/bin/activate
python manage.py migrate
python manage.py runserver
```

### 2) Démarrer le frontend
```bash
cd frontend
npm run dev
```

Accès local frontend : `http://127.0.0.1:5173`

## Tests et qualité
### Backend
Commande Django standard disponible :
```bash
cd backend
python manage.py test
```

### Frontend
Scripts présents dans `frontend/package.json` :
```bash
cd frontend
npm run lint
npm run preview
```

> Aucun script `test` n’est défini actuellement côté frontend.

## Build
Build frontend :
```bash
cd frontend
npm run build
```

## Déploiement (éléments présents dans le dépôt)
Le dépôt contient des fichiers de configuration Vercel :
- `frontend/vercel.json` (rewrites, dont `/api/*`)
- `backend/vercel.json` (configuration de fonction `config/wsgi.py`)

Le processus exact de déploiement (environnements, secrets, pipeline CI/CD) n’est pas documenté dans le dépôt et doit être complété selon votre infrastructure.

## API backend (aperçu)
Routes principales définies dans `backend/config/urls.py` :
- `/api/auth/`
- `/api/signalements/`
- `/api/commentaires/`
- `/api/votes/`
- `/api/admin/`
- `/api/chat/`

## Contribution
Aucune procédure formelle (`CONTRIBUTING.md`) n’est présente actuellement.

Pour contribuer proprement :
1. créer une branche,
2. faire des changements ciblés,
3. vérifier backend (`python manage.py test`) et frontend (`npm run lint`, `npm run build`),
4. ouvrir une pull request.
