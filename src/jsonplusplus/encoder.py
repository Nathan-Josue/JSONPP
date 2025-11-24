import orjson
import zstandard as zstd
import struct
import io
import math

ZSTD = zstd.ZstdCompressor(level=7)


# -----------------------------------------------------
#   TYPE DETECTION
# -----------------------------------------------------

def detect_numeric_type_int(values):
    """
    Détermine si une colonne d'entiers peut être stockée en int16 ou int32.
    """
    min_v = min(values)
    max_v = max(values)

    if -32768 <= min_v <= 32767 and -32768 <= max_v <= 32767:
        return "int16"
    return "int32"


def detect_numeric_type_float(values):
    """
    Détermine float16 si :
    - précision <= 3 décimales
    - valeur dans la plage float16
    Sinon float32.
    """
    # plage float16 IEEE754
    MIN_F16 = -65504
    MAX_F16 = 65504

    for v in values:
        if not (MIN_F16 <= v <= MAX_F16):
            return "float32"
        # précision <= 3 décimales
        if round(v, 3) != v:
            return "float32"

    return "float16"


def detect_type(values):
    """Détection du type avec support int16 / float16."""
    first = values[0]

    if isinstance(first, bool):
        return "bool"

    if isinstance(first, int):
        return detect_numeric_type_int(values)

    if isinstance(first, float):
        return detect_numeric_type_float(values)

    if isinstance(first, str):
        return "str"

    return "json"


# -----------------------------------------------------
#   PACKING
# -----------------------------------------------------

def pack_column(values, col_type):
    """Encode binaire en fonction du type."""
    if col_type == "int16":
        return struct.pack(f"{len(values)}h", *values)

    if col_type == "int32":
        return struct.pack(f"{len(values)}i", *values)

    if col_type == "float16":
        # conversion manuelle float32 -> float16 (IEEE754 half)
        import numpy as np
        arr = np.array(values, dtype=np.float16)
        return arr.tobytes()

    if col_type == "float32":
        return struct.pack(f"{len(values)}f", *values)

    if col_type == "bool":
        return bytes((1 if v else 0) for v in values)

    return orjson.dumps(values)


# -----------------------------------------------------
#   ENCODER PRINCIPAL
# -----------------------------------------------------

def encode_to_bytes(json_data):
    if not isinstance(json_data, list) or len(json_data) == 0:
        raise ValueError("Le JSON doit être une liste non vide")

    fields = list(json_data[0].keys())
    columns = {f: [row[f] for row in json_data] for f in fields}

    # Détection complète
    types = {f: detect_type(col) for f, col in columns.items()}

    # Compression colonnes
    compressed_columns = {}
    for f in fields:
        blob = pack_column(columns[f], types[f])
        compressed_columns[f] = ZSTD.compress(blob)

    # Index auto (numériques uniquement)
    indexes = {}
    for f, t in types.items():
        if t in ("int16", "int32", "float16", "float32"):
            sorted_idx = sorted(range(len(columns[f])),
                                key=lambda i: columns[f][i])
            indexes[f] = ZSTD.compress(orjson.dumps(sorted_idx))

    out = io.BytesIO()

    # Header
    out.write(b"JONX")
    out.write(struct.pack("I", 1))

    # Schema
    schema = {"fields": fields, "types": types}
    schema_bytes = ZSTD.compress(orjson.dumps(schema))
    out.write(struct.pack("I", len(schema_bytes)))
    out.write(schema_bytes)

    # Colonnes
    for f in fields:
        col = compressed_columns[f]
        out.write(struct.pack("I", len(col)))
        out.write(col)

    # Index
    out.write(struct.pack("I", len(indexes)))
    for f, idx in indexes.items():
        out.write(struct.pack("I", len(f)))
        out.write(f.encode("utf-8"))
        out.write(struct.pack("I", len(idx)))
        out.write(idx)

    return out.getvalue()


# -----------------------------------------------------
#   WRAPPER FICHIER
# -----------------------------------------------------

def jonx_encode(json_path, jonx_path):
    with open(json_path, "rb") as f:
        data = orjson.loads(f.read())

    jonx_bytes = encode_to_bytes(data)

    with open(jonx_path, "wb") as f:
        f.write(jonx_bytes)

    print(f"✅ JONX créé : {len(data)} lignes, {len(data[0])} colonnes")
