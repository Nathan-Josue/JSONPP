# Liste complète des opérations JONX sur un fichier JSON++

## 📋 Vue d'ensemble

Toutes les opérations disponibles pour manipuler un fichier JONX (JSON++) sont accessibles via la classe `JONXFile` et la fonction `decode_from_bytes()`.

---

## 🔧 Opérations de base

### 1. Chargement d'un fichier JONX

#### `JONXFile(path: str)`
**Description :** Charge un fichier JONX en mémoire (chargement paresseux)

**Paramètres :**
- `path` (str) : Chemin vers le fichier JONX

**Propriétés disponibles après chargement :**
- `fields` (list) : Liste des noms de colonnes disponibles
- `types` (dict) : Dictionnaire des types par colonne
- `indexes` (dict) : Dictionnaire des index disponibles

**Exemple :**
```python
file = JONXFile("data.jonx")
print(file.fields)  # ['id', 'name', 'age', 'price']
print(file.types)   # {'id': 'int32', 'name': 'str', ...}
```

---

## 📊 Opérations d'accès aux données

### 2. `get_column(field_name: str) -> list`
**Description :** Récupère une colonne décompressée (décompression à la demande)

**Paramètres :**
- `field_name` (str) : Nom de la colonne à récupérer

**Retourne :**
- `list` : Liste des valeurs de la colonne

**Performance :** O(n) - Décompression à la demande

**Exemple :**
```python
prices = file.get_column("price")
# Retourne: [100.5, 200.75, 150.0, ...]
```

### 3. `get_columns(field_names: list) -> dict`
**Description :** Récupère plusieurs colonnes en une seule opération

**Paramètres :**
- `field_names` (list) : Liste des noms de colonnes à récupérer

**Retourne :**
- `dict` : Dictionnaire {nom_colonne: [valeurs]}

**Performance :** O(n×m) où m = nombre de colonnes

**Exemple :**
```python
columns = file.get_columns(["id", "name", "price"])
# Retourne: {"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"], "price": [100, 200, 300]}
```

---

## 🔍 Opérations de recherche

### 4. `find_min(field: str, column=None, use_index=False) -> any`
**Description :** Trouve la valeur minimale d'une colonne

**Paramètres :**
- `field` (str) : Nom de la colonne
- `column` (list, optionnel) : Colonne pré-chargée (récupérée automatiquement si None)
- `use_index` (bool) : Utiliser l'index pour une recherche O(1)

**Retourne :**
- Valeur minimale de la colonne

**Performance :**
- O(1) avec index (ultra-rapide)
- O(n) sans index

**Exemple :**
```python
min_price = file.find_min("price", use_index=True)  # Ultra-rapide
# Retourne: 10.5
```

### 5. `find_max(field: str, column=None, use_index=False) -> any`
**Description :** Trouve la valeur maximale d'une colonne

**Paramètres :**
- `field` (str) : Nom de la colonne
- `column` (list, optionnel) : Colonne pré-chargée
- `use_index` (bool) : Utiliser l'index pour une recherche O(1)

**Retourne :**
- Valeur maximale de la colonne

**Performance :**
- O(1) avec index (ultra-rapide)
- O(n) sans index

**Exemple :**
```python
max_age = file.find_max("age", use_index=True)
# Retourne: 65
```

---

## 📈 Opérations d'agrégation

### 6. `sum(field: str, column=None) -> number`
**Description :** Calcule la somme d'une colonne numérique

**Paramètres :**
- `field` (str) : Nom de la colonne numérique
- `column` (list, optionnel) : Colonne pré-chargée

**Retourne :**
- Somme des valeurs de la colonne

**Performance :** O(n)

**Restrictions :** Colonne doit être numérique (int16, int32, float16, float32)

**Exemple :**
```python
total_sales = file.sum("sales")
# Retourne: 125000.5
```

### 7. `avg(field: str, column=None) -> float`
**Description :** Calcule la moyenne d'une colonne numérique

**Paramètres :**
- `field` (str) : Nom de la colonne numérique
- `column` (list, optionnel) : Colonne pré-chargée

**Retourne :**
- Moyenne des valeurs de la colonne

**Performance :** O(n)

**Restrictions :** Colonne doit être numérique et non vide

**Exemple :**
```python
avg_price = file.avg("price")
# Retourne: 150.25
```

### 8. `count(field: str = None) -> int`
**Description :** Compte le nombre d'éléments dans une colonne ou le nombre total de lignes

**Paramètres :**
- `field` (str, optionnel) : Nom de la colonne (si None, retourne le nombre total de lignes)

**Retourne :**
- Nombre d'éléments dans la colonne ou nombre total de lignes

**Performance :** O(1)

**Exemple :**
```python
total_rows = file.count()        # Nombre total de lignes
price_count = file.count("price")  # Nombre d'éléments dans la colonne price
```

---

## 🛠️ Opérations utilitaires

### 9. `info() -> dict`
**Description :** Retourne toutes les métadonnées du fichier JONX

**Retourne :**
- `dict` avec :
  - `path` (str) : Chemin du fichier
  - `version` (int) : Version du format JONX
  - `num_rows` (int) : Nombre de lignes
  - `num_columns` (int) : Nombre de colonnes
  - `fields` (list) : Liste des noms de colonnes
  - `types` (dict) : Dictionnaire des types par colonne
  - `indexes` (list) : Liste des colonnes avec index
  - `file_size` (int) : Taille du fichier en bytes

**Performance :** O(1)

**Exemple :**
```python
metadata = file.info()
print(f"Lignes: {metadata['num_rows']}")
print(f"Colonnes: {metadata['num_columns']}")
print(f"Taille: {metadata['file_size']} bytes")
```

### 10. `has_index(field: str) -> bool`
**Description :** Vérifie si une colonne a un index disponible

**Paramètres :**
- `field` (str) : Nom de la colonne à vérifier

**Retourne :**
- `bool` : True si la colonne a un index, False sinon

**Performance :** O(1)

**Exemple :**
```python
if file.has_index("price"):
    print("La colonne 'price' a un index")
```

### 11. `is_numeric(field: str) -> bool`
**Description :** Vérifie si une colonne est de type numérique

**Paramètres :**
- `field` (str) : Nom de la colonne à vérifier

**Retourne :**
- `bool` : True si la colonne est numérique, False sinon

**Performance :** O(1)

**Types numériques supportés :** int16, int32, float16, float32

**Exemple :**
```python
if file.is_numeric("price"):
    total = file.sum("price")
```

### 12. `check_schema() -> dict`
**Description :** Vérifie la cohérence du schéma du fichier JONX

**Retourne :**
- `dict` avec :
  - `valid` (bool) : True si le schéma est valide
  - `errors` (list) : Liste des erreurs trouvées
  - `warnings` (list) : Liste des avertissements

**Performance :** O(n) - Vérifie toutes les colonnes

**Exemple :**
```python
schema_check = file.check_schema()
if not schema_check["valid"]:
    print("Erreurs:", schema_check["errors"])
```

### 13. `validate() -> dict`
**Description :** Valide l'intégrité complète du fichier JONX

**Retourne :**
- `dict` avec :
  - `valid` (bool) : True si le fichier est valide
  - `errors` (list) : Liste des erreurs trouvées
  - `warnings` (list) : Liste des avertissements

**Performance :** O(n) - Validation complète

**Vérifications effectuées :**
- Cohérence du schéma
- Intégrité des données
- Décompression de toutes les colonnes
- Validation des index
- Cohérence des types

**Exemple :**
```python
validation = file.validate()
if validation["valid"]:
    print("✅ Fichier valide")
else:
    print("❌ Erreurs:", validation["errors"])
```

---

## 🔄 Opérations de décodage complet

### 14. `decode_from_bytes(data: bytes) -> dict`
**Description :** Décode des bytes JONX et retourne un dictionnaire avec les données JSON reconstruites

**Paramètres :**
- `data` (bytes) : Données JONX à décoder

**Retourne :**
- `dict` avec :
  - `version` (int) : Version du format JONX
  - `fields` (list) : Liste des noms de colonnes
  - `types` (dict) : Dictionnaire des types par colonne
  - `num_rows` (int) : Nombre de lignes
  - `json_data` (list) : Données JSON reconstruites (liste d'objets)

**Performance :** O(n) - Décompression de toutes les colonnes

**Exemple :**
```python
with open("data.jonx", "rb") as f:
    result = decode_from_bytes(f.read())

print(result["json_data"])  # Liste complète d'objets JSON
print(result["fields"])     # ["id", "name", ...]
print(result["types"])      # {"id": "int32", "name": "str", ...}
```

---

## 📊 Tableau récapitulatif

| # | Opération | Type | Description | Performance | Restrictions |
|---|-----------|------|-------------|-------------|--------------|
| 1 | `JONXFile()` | Chargement | Charge un fichier JONX | O(1) | - |
| 2 | `get_column()` | Accès | Récupère une colonne | O(n) | - |
| 3 | `get_columns()` | Accès | Récupère plusieurs colonnes | O(n×m) | - |
| 4 | `find_min()` | Recherche | Valeur minimale | O(1) avec index, O(n) sans | - |
| 5 | `find_max()` | Recherche | Valeur maximale | O(1) avec index, O(n) sans | - |
| 6 | `sum()` | Agrégation | Somme d'une colonne | O(n) | Colonne numérique uniquement |
| 7 | `avg()` | Agrégation | Moyenne d'une colonne | O(n) | Colonne numérique uniquement |
| 8 | `count()` | Agrégation | Nombre d'éléments | O(1) | - |
| 9 | `info()` | Utilitaire | Métadonnées complètes | O(1) | - |
| 10 | `has_index()` | Utilitaire | Vérifie si index existe | O(1) | - |
| 11 | `is_numeric()` | Utilitaire | Vérifie si colonne numérique | O(1) | - |
| 12 | `check_schema()` | Utilitaire | Vérifie le schéma | O(n) | - |
| 13 | `validate()` | Utilitaire | Valide l'intégrité | O(n) | - |
| 14 | `decode_from_bytes()` | Décodage | Décodage complet | O(n) | - |

**Légende :**
- `n` = nombre de lignes
- `m` = nombre de colonnes à récupérer

---

## 🎯 Opérations par catégorie

### Accès aux données
- `get_column()` - Récupérer une colonne
- `get_columns()` - Récupérer plusieurs colonnes
- `decode_from_bytes()` - Décodage complet

### Recherche
- `find_min()` - Valeur minimale
- `find_max()` - Valeur maximale

### Agrégation
- `sum()` - Somme
- `avg()` - Moyenne
- `count()` - Comptage

### Utilitaires
- `info()` - Métadonnées
- `has_index()` - Vérification d'index
- `is_numeric()` - Vérification de type
- `check_schema()` - Vérification du schéma
- `validate()` - Validation complète

---

## 📝 Notes importantes

1. **Chargement paresseux** : Les colonnes ne sont décompressées qu'à la demande
2. **Index automatiques** : Les colonnes numériques ont automatiquement un index trié
3. **Performance** : Utiliser `use_index=True` pour les opérations min/max sur colonnes numériques
4. **Validation** : Toutes les opérations valident automatiquement les paramètres
5. **Gestion d'erreurs** : Exceptions personnalisées avec messages détaillés

---

**Total : 14 opérations principales disponibles sur un fichier JONX**

