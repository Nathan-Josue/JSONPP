from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from logical.encoder import detect_type, pack_column, encode_to_bytes
from logical.decoder import decode_from_bytes
import orjson
import zstandard as zstd
from fastapi.responses import RedirectResponse

# Configuration de l'API
app = FastAPI(
    title="JONX API - Convertisseur JSON ↔ JSON++",
    description="""
    API REST complète pour convertir entre JSON et JSON++ (JONX), un format de fichier optimisé.
    
    ## 🚀 Fonctionnalités
    
    - **Encodage** : Convertir JSON → JONX (upload fichier ou body JSON)
    - **Décodage** : Convertir JONX → JSON avec métadonnées complètes
    - **Prévisualisation** : Analyser les métadonnées sans générer le fichier
    - **Health Check** : Vérifier l'état de l'API
    
    ## 📦 Format JONX
    
    Format binaire optimisé utilisant :
    - Compression zstd pour réduire la taille
    - Stockage en colonnes pour meilleure compression
    - Types optimisés (int32, float32, bool, str, json)
    - Index automatiques pour recherches rapides
    
    ## 🔗 Documentation
    
    - **Swagger UI** : `/docs` - Interface interactive pour tester l'API
    - **ReDoc** : `/redoc` - Documentation alternative
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    tags_metadata=[
        {
            "name": "Système",
            "description": "Endpoints système pour le monitoring et la santé de l'API"
        },
        {
            "name": "Encodage",
            "description": "Endpoints pour encoder des données JSON en format JONX optimisé"
        },
        {
            "name": "Décodage",
            "description": "Endpoints pour décoder des fichiers JONX et reconstruire le JSON original"
        },
        {
            "name": "Utilitaires",
            "description": "Endpoints utilitaires pour analyser et prévisualiser les données"
        }
    ]
)

# Configuration CORS pour permettre les requêtes depuis n'importe quelle origine
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles Pydantic pour les requêtes
class PreviewRequest(BaseModel):
    """
    Modèle pour la requête de prévisualisation
    
    Attributes:
        data: Liste de dictionnaires JSON représentant les données à analyser
    """
    data: List[Dict[str, Any]]
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": [
                    {"id": 1, "name": "Produit 1", "price": 100.50, "active": True},
                    {"id": 2, "name": "Produit 2", "price": 200.75, "active": False}
                ]
            }
        }

class EncodeRequest(BaseModel):
    """
    Modèle pour l'encodage JSON direct (alternative à l'upload de fichier)
    
    Attributes:
        data: Liste de dictionnaires JSON à encoder en format JONX
    """
    data: List[Dict[str, Any]]
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": [
                    {"id": 1, "name": "Produit 1", "price": 100.50, "active": True},
                    {"id": 2, "name": "Produit 2", "price": 200.75, "active": False}
                ]
            }
        }




# ==================== ENDPOINTS API ====================

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get(
    "/health",
    summary="Vérification de santé",
    description="Endpoint de santé pour vérifier que l'API est opérationnelle. Utile pour les systèmes de monitoring et les health checks.",
    tags=["Système"],
    response_description="Statut de santé de l'API"
)
async def health_check():
    """
    Vérifie l'état de santé de l'API
    
    Cet endpoint retourne des informations sur l'état de l'API et peut être utilisé
    par des systèmes de monitoring pour vérifier la disponibilité du service.
    
    Returns:
        dict: Dictionnaire contenant :
            - status (str): Statut de santé ("healthy")
            - service (str): Nom du service
            - version (str): Version de l'API
    
    Example:
        ```bash
        curl http://localhost:8000/health
        ```
        
        Réponse:
        ```json
        {
            "status": "healthy",
            "service": "JONX API",
            "version": "1.0.0"
        }
        ```
    """
    return {
        "status": "healthy",
        "service": "JONX API",
        "version": "1.0.0"
    }


@app.post(
    "/api/encode",
    summary="Encoder JSON → JONX (upload fichier)",
    description="""
    Encode un fichier JSON en format JONX optimisé.
    
    **Fonctionnalités :**
    - Détection automatique des types de colonnes (int32, float32, str, bool, json)
    - Compression zstd pour réduire la taille du fichier
    - Création automatique d'index pour les colonnes numériques
    - Stockage en colonnes pour une meilleure compression
    
    **Format d'entrée :**
    - Le fichier JSON doit être une liste d'objets (array)
    - Tous les objets doivent avoir les mêmes clés
    - Les types sont détectés automatiquement à partir de la première valeur
    
    **Format de sortie :**
    - Fichier binaire `.json++` téléchargeable
    - Le nom du fichier de sortie est basé sur le nom du fichier d'entrée
    """,
    tags=["Encodage"],
    response_description="Fichier JONX binaire en téléchargement"
)
async def encode(file: UploadFile = File(..., description="Fichier JSON à encoder (format: liste d'objets)")):
    """
    Encode un fichier JSON en format JONX via upload de fichier
    
    Cet endpoint accepte un fichier JSON via multipart/form-data et le convertit
    en format JONX optimisé. Le fichier résultant est retourné en téléchargement.
    
    Args:
        file: Fichier JSON à encoder (doit être une liste d'objets)
    
    Returns:
        Response: Fichier binaire `.json++` avec headers de téléchargement
    
    Raises:
        HTTPException 400: 
            - Si aucun fichier n'est fourni
            - Si le JSON n'est pas une liste d'objets
            - Si la liste est vide
            - Si le JSON est malformé
        HTTPException 500: Erreur interne lors de l'encodage
    
    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/encode" \\
             -F "file=@data.json"
        ```
        
        Avec Python requests:
        ```python
        import requests
        
        with open("data.json", "rb") as f:
            response = requests.post(
                "http://localhost:8000/api/encode",
                files={"file": f}
            )
        
        with open("output.json++", "wb") as out:
            out.write(response.content)
        ```
        
        Format JSON d'entrée attendu:
        ```json
        [
            {"id": 1, "name": "Produit 1", "price": 100.50, "active": True},
            {"id": 2, "name": "Produit 2", "price": 200.75, "active": False}
        ]
        ```
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Aucun fichier sélectionné")

        # Lire et parser le JSON
        file_data = await file.read()
        json_data = orjson.loads(file_data)

        if not isinstance(json_data, list):
            raise HTTPException(status_code=400, detail="Le JSON doit être une liste d'objets")

        if len(json_data) == 0:
            raise HTTPException(status_code=400, detail="La liste JSON ne peut pas être vide")

        # Encoder en format JONX
        jonx_bytes = encode_to_bytes(json_data)

        # Générer le nom du fichier de sortie
        output_filename = file.filename.rsplit('.', 1)[0] + '.json++'

        # Retourner le fichier en tant que réponse
        return Response(
            content=jonx_bytes,
            media_type='application/octet-stream',
            headers={
                "Content-Disposition": f'attachment; filename="{output_filename}"'
            }
        )

    except orjson.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Erreur de parsing JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'encodage: {str(e)}")


@app.post(
    "/api/encode/json",
    summary="Encoder JSON → JONX (body JSON)",
    description="""
    Encode des données JSON envoyées dans le body de la requête en format JONX.
    
    **Alternative à l'upload de fichier :**
    Cette endpoint permet d'encoder des données JSON directement depuis le body
    de la requête, sans avoir besoin d'un fichier. Utile pour les intégrations
    programmatiques et les applications web.
    
    **Avantages :**
    - Pas besoin de créer un fichier temporaire
    - Idéal pour les données générées dynamiquement
    - Même compression et optimisation que l'endpoint `/api/encode`
    
    **Format d'entrée :**
    - Body JSON avec une clé `data` contenant une liste d'objets
    - Content-Type: `application/json`
    """,
    tags=["Encodage"],
    response_description="Fichier JONX binaire en téléchargement"
)
async def encode_from_json(request: EncodeRequest):
    """
    Encode des données JSON (envoyées dans le body) en format JONX
    
    Cet endpoint accepte des données JSON directement dans le body de la requête
    et les convertit en format JONX. C'est une alternative à l'upload de fichier
    pour les cas où les données sont déjà en mémoire.
    
    Args:
        request: Objet EncodeRequest contenant les données JSON à encoder
    
    Returns:
        Response: Fichier binaire `.json++` avec le nom "output.json++"
    
    Raises:
        HTTPException 400: 
            - Si le JSON n'est pas une liste d'objets
            - Si la liste est vide
        HTTPException 500: Erreur interne lors de l'encodage
    
    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/encode/json" \\
             -H "Content-Type: application/json" \\
             -d '{
               "data": [
                 {"id": 1, "name": "Produit 1", "price": 100.50},
                 {"id": 2, "name": "Produit 2", "price": 200.75}
               ]
             }' \\
             --output output.json++
        ```
        
        Avec Python requests:
        ```python
        import requests
        
        data = {
            "data": [
                {"id": 1, "name": "Produit 1", "price": 100.50, "active": True},
                {"id": 2, "name": "Produit 2", "price": 200.75, "active": False}
            ]
        }
        
        response = requests.post(
            "http://localhost:8000/api/encode/json",
            json=data
        )
        
        with open("output.json++", "wb") as f:
            f.write(response.content)
        ```
    """
    try:
        json_data = request.data

        if not isinstance(json_data, list):
            raise HTTPException(status_code=400, detail="Le JSON doit être une liste d'objets")

        if len(json_data) == 0:
            raise HTTPException(status_code=400, detail="La liste JSON ne peut pas être vide")

        # Encoder en format JONX
        jonx_bytes = encode_to_bytes(json_data)

        # Retourner le fichier en tant que réponse
        return Response(
            content=jonx_bytes,
            media_type='application/octet-stream',
            headers={
                "Content-Disposition": 'attachment; filename="output.json++"'
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'encodage: {str(e)}")


@app.post(
    "/api/decode",
    summary="Décoder JONX → JSON",
    description="""
    Décode un fichier JONX et retourne les données JSON reconstruites avec les métadonnées.
    
    **Fonctionnalités :**
    - Décompression automatique des colonnes
    - Reconstruction complète du JSON original
    - Retourne les métadonnées (champs, types, version, nombre de lignes)
    - Validation du format JONX
    
    **Format de sortie :**
    - JSON avec toutes les métadonnées du fichier JONX
    - Données JSON reconstruites dans `json_data`
    - Informations sur la structure (fields, types, num_rows)
    """,
    tags=["Décodage"],
    response_description="Dictionnaire JSON contenant les métadonnées et les données décodées"
)
async def decode(file: UploadFile = File(..., description="Fichier JONX à décoder (extension .json++ ou .jonx)")):
    """
    Décode un fichier JONX et retourne les données JSON avec métadonnées
    
    Cet endpoint accepte un fichier JONX et le décode pour reconstruire le JSON original.
    Il retourne également toutes les métadonnées du fichier (schéma, types, version, etc.).
    
    Args:
        file: Fichier JONX à décoder (format binaire `.json++` ou `.jonx`)
    
    Returns:
        dict: Dictionnaire contenant :
            - success (bool): Indicateur de succès
            - file_name (str): Nom du fichier uploadé
            - file_size (int): Taille du fichier en bytes
            - version (int): Version du format JONX
            - fields (list): Liste des noms de colonnes
            - types (dict): Dictionnaire des types par colonne
            - num_rows (int): Nombre de lignes de données
            - json_data (list): Données JSON reconstruites
    
    Raises:
        HTTPException 400: 
            - Si aucun fichier n'est fourni
            - Si le fichier n'est pas au format JONX valide
        HTTPException 500: Erreur interne lors du décodage
    
    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/decode" \\
             -F "file=@data.json++" \\
             -o result.json
        ```
        
        Avec Python requests:
        ```python
        import requests
        import json
        
        with open("data.json++", "rb") as f:
            response = requests.post(
                "http://localhost:8000/api/decode",
                files={"file": f}
            )
        
        result = response.json()
        print(f"Colonnes: {result['fields']}")
        print(f"Types: {result['types']}")
        print(f"Nombre de lignes: {result['num_rows']}")
        print(f"Données: {json.dumps(result['json_data'], indent=2)}")
        ```
        
        Réponse JSON:
        ```json
        {
            "success": true,
            "file_name": "data.json++",
            "file_size": 273,
            "version": 1,
            "fields": ["id", "name", "price", "active"],
            "types": {
                "id": "int32",
                "name": "str",
                "price": "float32",
                "active": "bool"
            },
            "num_rows": 2,
            "json_data": [
                {"id": 1, "name": "Produit 1", "price": 100.50, "active": true},
                {"id": 2, "name": "Produit 2", "price": 200.75, "active": false}
            ]
        }
        ```
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Aucun fichier sélectionné")
        
        # Lire les données du fichier
        file_data = await file.read()
        
        # Décoder le fichier JONX
        result = decode_from_bytes(file_data)
        
        return {
            "success": True,
            "file_name": file.filename,
            "file_size": len(file_data),
            "version": result["version"],
            "fields": result["fields"],
            "types": result["types"],
            "num_rows": result["num_rows"],
            "json_data": result["json_data"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du décodage: {str(e)}")


@app.post(
    "/api/preview",
    summary="Prévisualiser les métadonnées JONX",
    description="""
    Prévisualise les métadonnées et estime la taille d'un fichier JONX sans le générer.
    
    **Utilité :**
    - Voir quels types seront détectés pour chaque colonne
    - Estimer la taille du fichier JONX qui serait généré
    - Valider la structure des données avant l'encodage
    - Obtenir les métadonnées sans consommer de ressources pour l'encodage complet
    
    **Informations retournées :**
    - Liste des colonnes détectées
    - Types automatiquement détectés pour chaque colonne
    - Nombre de lignes
    - Taille estimée du fichier JONX (en bytes)
    - Version du format qui serait utilisée
    
    **Détection automatique des types :**
    - `int32`: Entiers
    - `float32`: Nombres décimaux
    - `str`: Chaînes de caractères
    - `bool`: Booléens
    - `json`: Objets complexes (fallback)
    """,
    tags=["Utilitaires"],
    response_description="Métadonnées et estimation de taille du fichier JONX"
)
async def preview(request: PreviewRequest):
    """
    Prévisualise les métadonnées JONX sans générer le fichier
    
    Cet endpoint analyse les données JSON fournies et retourne les métadonnées
    qui seraient utilisées lors de l'encodage, ainsi qu'une estimation de la
    taille du fichier JONX résultant. Aucun fichier n'est généré, ce qui
    permet d'analyser rapidement la structure des données.
    
    Args:
        request: Objet PreviewRequest contenant les données JSON à analyser
    
    Returns:
        dict: Dictionnaire contenant :
            - success (bool): Indicateur de succès
            - version (int): Version du format JONX
            - fields (list): Liste des noms de colonnes détectées
            - types (dict): Dictionnaire des types détectés par colonne
            - num_rows (int): Nombre de lignes de données
            - estimated_size (int): Taille estimée du fichier JONX en bytes
    
    Raises:
        HTTPException 400: 
            - Si la liste JSON est vide
        HTTPException 500: Erreur interne lors de l'analyse
    
    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/preview" \\
             -H "Content-Type: application/json" \\
             -d '{
               "data": [
                 {"id": 1, "name": "Produit 1", "price": 100.50, "active": true},
                 {"id": 2, "name": "Produit 2", "price": 200.75, "active": false}
               ]
             }'
        ```
        
        Avec Python requests:
        ```python
        import requests
        
        data = {
            "data": [
                {"id": 1, "name": "Produit 1", "price": 100.50, "active": True},
                {"id": 2, "name": "Produit 2", "price": 200.75, "active": False}
            ]
        }
        
        response = requests.post(
            "http://localhost:8000/api/preview",
            json=data
        )
        
        result = response.json()
        print(f"Colonnes détectées: {result['fields']}")
        print(f"Types: {result['types']}")
        print(f"Taille estimée: {result['estimated_size']} bytes")
        ```
        
        Réponse JSON:
        ```json
        {
            "success": true,
            "version": 1,
            "fields": ["id", "name", "price", "active"],
            "types": {
                "id": "int32",
                "name": "str",
                "price": "float32",
                "active": "bool"
            },
            "num_rows": 2,
            "estimated_size": 273
        }
        ```
    """
    try:
        data = request.data
        if len(data) == 0:
            raise HTTPException(status_code=400, detail="La liste JSON ne peut pas être vide")
        
        # Détection automatique des colonnes
        fields = list(data[0].keys())
        columns = {field: [p.get(field) for p in data] for field in fields}
        
        # Détection des types
        types = {field: detect_type(vals) for field, vals in columns.items()}
        
        # Estimer la taille (approximation)
        c = zstd.ZstdCompressor(level=3)
        estimated_size = 8  # Header
        schema = {"fields": fields, "types": types}
        schema_compressed = c.compress(orjson.dumps(schema))
        estimated_size += 4 + len(schema_compressed)  # Schema
        
        for field in fields:
            packed = pack_column(columns[field], types[field])
            compressed = c.compress(packed)
            estimated_size += 4 + len(compressed)  # Colonne
        
        # Index (approximation)
        num_indexes = sum(1 for t in types.values() if t in ["int32", "float32"])
        estimated_size += 4  # Nombre d'index
        for field, col_type in types.items():
            if col_type in ["int32", "float32"]:
                sorted_index = sorted(range(len(columns[field])), key=lambda i: columns[field][i])
                idx_compressed = c.compress(orjson.dumps(sorted_index))
                estimated_size += 4 + len(field.encode("utf-8")) + 4 + len(idx_compressed)
        
        return {
            "success": True,
            "version": 1,
            "fields": fields,
            "types": types,
            "num_rows": len(data),
            "estimated_size": estimated_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la prévisualisation: {str(e)}")


if __name__ == '__main__':
    import uvicorn
    print("JONX|JSON++ API démarrée sur http://localhost:8000")
    print("Documentation disponible sur http://localhost:8000/docs")
    print("Redoc disponible sur http://localhost:8000/redoc")
    uvicorn.run(app, host="0.0.0.0", port=8000)
