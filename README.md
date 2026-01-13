# 🎬 CineFeels - Analyse de Films par Émotions

**CineFeels** est une plateforme innovante de recommandation de films basée sur l'analyse émotionnelle, utilisant l'intelligence artificielle.

---

## 📖 Description

CineFeels permet aux utilisateurs de découvrir des films parfaitement adaptés à leur état d'esprit. En sélectionnant leurs émotions actuelles avec des pourcentages personnalisés, l'application recommande des films correspondant à ce profil émotionnel.

### Fonctionnalités principales

- **Authentification sécurisée** : Inscription et connexion avec JWT
- **Dashboard personnalisé** : "Bonjour, [nom]" avec statistiques personnelles
- **Sélection multi-émotions** : 10 émotions avec sliders de pourcentage (0-100%)
  - Émotions de base : Joie, Tristesse, Peur, Colère, Surprise, Dégoût
  - Émotions CineFeels : Frisson, Romance, Humour, Inspiration
- **Radar Chart** : Visualisation graphique du profil émotionnel
- **Historique d'analyse** : Suivi des analyses passées
- **Détails de films** : Page complète avec analyse émotionnelle
- **Meilleurs films** : Recommandations personnalisées

---

## 🛠️ Technologies utilisées

| Composant | Technologies |
|-----------|-------------|
| **Backend** | Python, FastAPI, JWT, Pydantic |
| **Frontend** | HTML5, CSS3, JavaScript (Vanilla) |
| **IA** | BERT (analyse émotionnelle) |
| **Base de données** | MongoDB (films), JSON (utilisateurs) |
| **API externe** | TMDB (affiches de films) |

---

## 📁 Structure du projet

```
CineFeels/
├── backend/                    # API FastAPI
│   ├── main.py                # Point d'entrée
│   ├── api/routes/            # Routes API
│   │   ├── auth.py            # Authentification
│   │   ├── movies.py          # Films
│   │   └── recommendations.py # Recommandations
│   ├── services/              # Services métier
│   │   ├── user_service_simple.py
│   │   ├── emotion_service.py
│   │   └── recommendation_service.py
│   ├── models/                # Modèles Pydantic
│   └── config/                # Configuration
│
├── frontend_html/             # Interface utilisateur
│   ├── index.html             # Page principale
│   ├── style.css              # Styles
│   └── script.js              # Logique JavaScript
│
└── data/                      # Données persistantes
    └── users.json             # Utilisateurs
```

---

## 🚀 Installation et Démarrage

### Prérequis
- Python 3.9+
- pip

### 1. Cloner le projet
```bash
cd CineFeels
```

### 2. Installer les dépendances
```bash
cd backend
pip install -r requirements.txt
```

### 3. Lancer le Backend
```bash
python main.py
```
Le serveur démarre sur **http://localhost:8000**

### 4. Lancer le Frontend
```bash
cd frontend_html
python3 -m http.server 8080
```
L'application est accessible sur **http://localhost:8080**

---

## 🔗 Endpoints API

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/v1/auth/register` | Inscription |
| POST | `/api/v1/auth/login` | Connexion |
| GET | `/api/v1/auth/me` | Profil utilisateur |
| GET | `/api/v1/movies` | Liste des films |
| GET | `/api/v1/movies/{id}` | Détails d'un film |
| GET | `/api/v1/movies/{id}/emotions` | Émotions d'un film |
| POST | `/api/v1/recommendations/` | Recommandations par émotions |

📚 Documentation Swagger : **http://localhost:8000/docs**

---

## Utilisation

1. **Créer un compte** sur la page d'accueil
2. **Se connecter** pour accéder au dashboard
3. **Sélectionner vos émotions** avec les sliders (plusieurs simultanément)
4. **Obtenir des recommandations** de films adaptés
5. **Consulter les détails** en cliquant sur un film
6. **Suivre votre historique** et profil émotionnel

---

## Aperçu

### Page d'accueil
- Présentation de l'application CineFeels
- Formulaires de connexion et inscription
- Technologies utilisées

### Dashboard utilisateur
- Message de bienvenue personnalisé
- Statistiques (analyses, films découverts, favoris)
- Radar Chart du profil émotionnel
- Historique des analyses
- Sélecteur d'émotions avec 10 sliders

### Page de détail film
- Affiche et informations du film
- Note et année de sortie
- Synopsis complet
- Analyse émotionnelle avec barres de progression

---

## Auteur

Projet développé dans le cadre d'un projet académique.
Aouami Salma 
El Gharss Mohammed Amin 
Afriad Abdeslam 
Ela Jabbar Mohamed Houssam

---

## 📄 Licence

© 2025 CineFeels - Tous droits réservés

