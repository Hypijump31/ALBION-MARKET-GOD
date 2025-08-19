# 🏰 Albion Online Market Analyzer

Un analyseur de marché complet pour Albion Online avec calculs précis de rentabilité pour le raffinage et l'artisanat, intégrant les mécaniques réelles du jeu.

## ✨ Fonctionnalités Principales

### 📊 Analyse de Marché en Temps Réel
- **API Albion Online Data**: Intégration complète avec l'API officielle
- **Support Multi-Régions**: Europe, Amériques, Asie
- **Prix Actuels & Historiques**: Données de marché en temps réel
- **Visualisations Interactives**: Graphiques Plotly avec analyse de tendances

### 🔥 Calculateur de Raffinage Avancé
- **Mécaniques Précises**: Formule RRR = 1 - 1/(1 + 0.59 + LPB) avec focus
- **Bonus Locaux (LPB)**: Prise en compte des bonus de production par ville
- **Calculs de Focus**: Coûts optimisés selon spécialisation et premium
- **Analyse Multi-Villes**: Comparaison automatique des profits
- **Détection d'Arbitrage**: Opportunités de trading inter-villes

### 🔨 Calculateur d'Artisanat
- **Recettes Complètes**: Base de données des recettes d'artisanat
- **Bonus de Ville**: Réductions de ressources selon la spécialisation
- **Taux de Retour**: Calculs précis avec focus et spécialisations
- **Analyse de Rentabilité**: Coûts détaillés et marges de profit

### ⚙️ Configuration Avancée
- **Paramètres Joueur**: Premium, focus, spécialisations (0-100)
- **Bonus d'Équipement**: Trophées et nourriture
- **Taux de Taxe**: Configuration par ville
- **Multiplicateurs de Qualité**: Normal à Masterpiece

### 🚀 Optimisations de Performance
- **Cache Intelligent**: Mise en cache TTL pour les requêtes API
- **Traitement par Lots**: Optimisation mémoire pour gros datasets
- **Requêtes Parallèles**: API calls asynchrones et multi-threadées
- **Pagination**: Gestion efficace des résultats volumineux

### 🔍 Confirmation des Requêtes API
- **Mode Debug**: Détails complets avant chaque requête
- **Contrôle Utilisateur**: Confirmation manuelle optionnelle
- **Métriques Performance**: Suivi des appels API et cache

## 🛠️ Installation

### Prérequis
- Python 3.8+
- pip package manager

### Installation Rapide
```bash
# Cloner le repository
git clone <repository-url>
cd windsurf-project

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
streamlit run app.py
```

### Installation avec Environnement Virtuel (Recommandé)
```bash
# Créer un environnement virtuel
python -m venv .venv

# Activer l'environnement (Windows)
.venv\Scripts\activate
# Ou sur Linux/Mac
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
streamlit run app.py
```

## 🚀 Utilisation

### Interface Principale
1. **Configuration**: Paramétrez votre compte, serveur, et préférences
2. **Analyse de Raffinage**: Calculez la rentabilité du raffinage en temps réel
3. **Analyse d'Artisanat**: Optimisez vos profits d'artisanat
4. **Analyse de Marché**: Visualisez les tendances et opportunités

### Configuration Recommandée
1. Sélectionnez votre serveur (Europe/Amériques/Asie)
2. Configurez votre statut premium et points de focus
3. Définissez vos niveaux de spécialisation
4. Ajustez les bonus d'équipement et nourriture

### Workflow Typique
1. **Configuration**: Définir vos paramètres dans l'onglet Configuration
2. **Sélection**: Choisir ressource/recette et ville d'analyse
3. **Prix**: Récupération automatique via API (ou saisie manuelle)
4. **Calcul**: Analyse automatique de rentabilité
5. **Optimisation**: Comparaison entre villes et détection d'arbitrage

## 📁 Structure du Projet

```
windsurf-project/
├── src/
│   ├── __init__.py
│   ├── data_collector.py       # Collecte de données API
│   ├── analyzer.py            # Analyses de marché
│   ├── visualization.py       # Visualisations Plotly
│   ├── config.py             # Gestion configuration
│   ├── refining_calculator.py # Calculs de raffinage
│   ├── crafting_calculator.py # Calculs d'artisanat
│   ├── price_manager.py      # Gestion des prix
│   ├── item_mapping.py       # Mapping des objets
│   └── performance_optimizer.py # Optimisations performance
├── pages/
│   ├── config.py            # Page de configuration
│   ├── refining_analysis.py # Analyse de raffinage
│   └── crafting_analysis.py # Analyse d'artisanat
├── app.py                   # Application Streamlit principale
├── requirements.txt         # Dépendances Python
├── config.json             # Configuration utilisateur
└── README.md              # Documentation
```

## ⚙️ Configuration Avancée

### Paramètres API
- **Rate Limiting**: 180 requêtes/minute (limite API)
- **Cache TTL**: 5 minutes pour prix de raffinage, 3 minutes pour prix actuels
- **Timeout**: 30 secondes par requête
- **Retry Logic**: 3 tentatives avec backoff exponentiel

### Paramètres de Performance
- **Batch Size**: 100 éléments par lot
- **Max Workers**: 5 threads parallèles
- **Cache Size**: 1000 entrées maximum
- **Memory Optimization**: Compression automatique des DataFrames

### Variables d'Environnement (Optionnel)
```bash
# .env file
ALBION_API_REGION=Europe
DEFAULT_CITY=Caerleon
CACHE_TTL=300
MAX_CONCURRENT_REQUESTS=5
```

## 🔧 API Albion Online Data

### Endpoints Utilisés
- **Prix Actuels**: `/api/v2/stats/prices/{items}.json`
- **Historique**: `/api/v2/stats/history/{item}.json`
- **Prix de l'Or**: `/api/v2/stats/gold.json`

### Régions Supportées
- **Europe**: `europe.albion-online-data.com`
- **Amériques**: `west.albion-online-data.com` 
- **Asie**: `east.albion-online-data.com`

## 🧮 Formules de Calcul

### Raffinage
```
Return Rate avec Focus = 1 - 1/(1 + 0.59 + LPB)
LPB = Local Production Bonus (varie par ville et ressource)
Focus Cost = Base Cost * (1 - Specialization/100 * 0.5)
Profit Net = (Quantité Produite * Prix Vente) - (Coût Matériaux + Taxes)
```

### Artisanat
```
Return Rate = Base Rate + (Specialization/100 * 0.30) + (Focus ? 0.35 : 0)
Items Produits = Quantité * (1 + Return Rate)
Coût Matériaux = Σ(Quantité Matériau * (1 - Bonus Ville) * Prix)
```

## 🎯 Mécaniques du Jeu Implémentées

### Spécialisations
- **Levels 0-100**: Progression linéaire des bonus
- **Réduction Focus**: Jusqu'à 50% à niveau 100
- **Bonus Return Rate**: Jusqu'à 30% pour l'artisanat

### Bonus Premium
- **Efficacité Focus**: +5% d'efficacité (pas de return rate direct)
- **Multiplication Learning Points**: x2 gain d'expérience

### Bonus de Ville
- **Thetford**: Fiber/Cloth (15% réduction ressources)
- **Fort Sterling**: Ore/Metal (15% réduction ressources)
- **Lymhurst**: Wood (15% réduction ressources)
- **Bridgewatch**: Hide/Leather (15% réduction ressources)
- **Martlock**: Stone/Rock (15% réduction ressources)
- **Caerleon**: Taxes réduites (3.5% vs 4.5%)

## 🐛 Dépannage

### Problèmes Courants

**Erreur "No price data found"**
- Vérifiez la connexion internet
- Essayez un autre serveur (Europe/Amériques/Asie)
- Utilisez la saisie manuelle des prix

**Application lente**
- Videz le cache via le bouton dans la sidebar
- Réduisez le nombre d'éléments analysés simultanément
- Activez le mode confirmation API pour limiter les requêtes

**Calculs incorrects**
- Vérifiez vos paramètres de configuration
- Assurez-vous que les spécialisations sont correctement définies
- Consultez les logs pour les erreurs détaillées

### Logs de Debug
```bash
# Activer les logs détaillés
export PYTHONPATH=.
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
streamlit run app.py
```

## 🤝 Contribution

### Développement Local
```bash
# Fork et clone
git clone <your-fork>
cd windsurf-project

# Branche de développement
git checkout -b feature/nouvelle-fonctionnalite

# Installation en mode développement
pip install -e .

# Tests
python -m pytest tests/
```

### Guidelines
- Code en anglais, interface en français
- Docstrings obligatoires pour fonctions publiques
- Type hints recommandés
- Tests unitaires pour calculs critiques

## 📈 Roadmap

### Version 2.0 (Planifiée)
- [ ] Support des enchantements
- [ ] Calculs de transport
- [ ] Alerts prix personnalisées
- [ ] Export données CSV/Excel
- [ ] API REST intégrée

### Améliorations Futures
- [ ] Machine Learning pour prédictions de prix
- [ ] Interface mobile optimisée
- [ ] Intégration Discord Bot
- [ ] Base de données historique locale

## 📄 Licence

Ce projet est sous licence MIT. Voir `LICENSE` pour plus de détails.

## 🙏 Remerciements

- **Albion Online Data Project**: Pour l'API publique
- **Sandbox Interactive**: Pour Albion Online
- **Streamlit Team**: Pour le framework d'application
- **Communauté Albion**: Pour les retours et suggestions

---

**Version**: 1.0.0  
**Dernière Mise à Jour**: Août 2024  
**Compatibilité**: Albion Online - Toutes versions actuelles
