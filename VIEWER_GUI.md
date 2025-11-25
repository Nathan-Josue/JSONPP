# Visualiseur GUI JSON++

Application desktop moderne pour visualiser et explorer les fichiers JONX (JSON++).

## 🚀 Installation

### Installation avec support GUI

```bash
# Installation complète avec GUI
pip install jsonplusplus[gui]

# Ou installation séparée
pip install jsonplusplus
pip install customtkinter
```

## 💻 Utilisation

### Lancer le visualiseur

#### Méthode 1 : Via la commande CLI

```bash
# Ouvrir le visualiseur (sélectionner un fichier depuis l'interface)
jsonplusplus view

# Ouvrir directement un fichier
jsonplusplus view data.jonx
```

#### Méthode 2 : Commande dédiée

```bash
# Lancer le visualiseur standalone
jonx-viewer

# Ou avec un fichier
jonx-viewer data.jonx
```

#### Méthode 3 : Module Python

```bash
python -m jsonplusplus.viewer_main
python -m jsonplusplus.viewer_main data.jonx
```

## 🎨 Fonctionnalités

### Interface principale

- **Mode sombre/clair** : Basculez entre les thèmes
- **Tableau interactif** : Visualisation des données en tableau
- **Pagination** : Navigation par pages (50, 100, 200, 500, 1000 lignes par page)
- **Recherche** : Recherche en temps réel dans toutes les colonnes
- **Métadonnées** : Panneau latéral avec toutes les informations du fichier
- **Statistiques** : Statistiques automatiques pour les colonnes numériques

### Panneau latéral (Métadonnées)

Affiche :
- **Informations du fichier** : Chemin, version, taille
- **Structure** : Nombre de lignes et colonnes
- **Liste des colonnes** : Avec types et indicateurs d'index
- **Statistiques** : Min, Max, Moyenne pour les colonnes numériques

### Barre d'outils

- **📂 Ouvrir** : Sélectionner un fichier JONX
- **🔍 Recherche** : Champ de recherche en temps réel
- **🔄 Actualiser** : Recharger le fichier actuel

### Menu

#### Fichier
- **Ouvrir...** (Ctrl+O) : Ouvrir un fichier JONX
- **Exporter en CSV...** : Exporter les données filtrées en CSV
- **Exporter en JSON...** : Exporter les données filtrées en JSON
- **Quitter** (Ctrl+Q) : Fermer l'application

#### Affichage
- **Mode clair** : Passer en mode clair
- **Mode sombre** : Passer en mode sombre
- **Actualiser** (F5) : Recharger les données

#### Aide
- **À propos** : Informations sur l'application

## 📊 Fonctionnalités avancées

### Pagination

- Navigation avec les boutons "Précédent" et "Suivant"
- Sélection du nombre de lignes par page (50, 100, 200, 500, 1000)
- Affichage du numéro de page actuel

### Recherche

- Recherche en temps réel dans toutes les colonnes
- Filtrage automatique des résultats
- Compteur de lignes filtrées

### Export

- **CSV** : Export des données filtrées au format CSV
- **JSON** : Export des données filtrées au format JSON
- Seules les données actuellement affichées/filtrées sont exportées

### Statistiques automatiques

Pour chaque colonne numérique, affichage automatique de :
- **Minimum** : Valeur minimale (utilise l'index si disponible)
- **Maximum** : Valeur maximale (utilise l'index si disponible)
- **Moyenne** : Moyenne arithmétique

## ⌨️ Raccourcis clavier

- **Ctrl+O** : Ouvrir un fichier
- **Ctrl+Q** : Quitter l'application
- **F5** : Actualiser les données

## 🎯 Cas d'usage

### Exploration rapide
1. Lancez le visualiseur
2. Ouvrez un fichier JONX
3. Parcourez les données avec la pagination
4. Utilisez la recherche pour trouver des valeurs spécifiques

### Analyse de données
1. Ouvrez votre fichier JONX
2. Consultez les statistiques dans le panneau latéral
3. Filtrez les données avec la recherche
4. Exportez les résultats en CSV ou JSON

### Validation de fichiers
1. Ouvrez le fichier JONX
2. Vérifiez les métadonnées dans le panneau latéral
3. Consultez la structure des colonnes
4. Vérifiez la cohérence des données

## 🐛 Dépannage

### Erreur : "customtkinter n'est pas installé"

**Solution :**
```bash
pip install customtkinter
# Ou
pip install jsonplusplus[gui]
```

### L'application ne démarre pas

**Vérifications :**
1. Python >= 3.8 installé
2. customtkinter installé
3. Fichier JONX valide

### Performance lente avec de gros fichiers

**Recommandations :**
- Utilisez la pagination (réduire le nombre de lignes par page)
- Utilisez la recherche pour filtrer les données
- Fermez les autres applications pour libérer de la RAM

## 📝 Notes techniques

- **Chargement paresseux** : Les colonnes ne sont décompressées qu'à la demande
- **Threading** : Le chargement des fichiers se fait en arrière-plan pour ne pas bloquer l'interface
- **Mémoire** : Seules les données de la page actuelle sont chargées en mémoire
- **Performance** : Optimisé pour fichiers jusqu'à plusieurs GB

## 🔮 Améliorations futures

- Graphiques et visualisations
- Filtres avancés par colonne
- Tri par colonne
- Comparaison de fichiers
- Mode plein écran
- Personnalisation des thèmes

---

**Version :** 1.0.7  
**Dépendances :** customtkinter >= 5.2.0

