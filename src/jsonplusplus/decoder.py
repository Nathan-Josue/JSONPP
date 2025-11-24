import orjson
import zstandard as zstd
import struct
import numpy as np


def decode_from_bytes(data: bytes) -> dict:
    if not data.startswith(b"JONX"):
        raise ValueError("Le fichier n'est pas au format JONX")

    version = struct.unpack("I", data[4:8])[0]
    c = zstd.ZstdDecompressor()
    offset = 8

    # --- Lire le schéma ---
    schema_size = struct.unpack("I", data[offset:offset + 4])[0]
    offset += 4
    schema = orjson.loads(c.decompress(data[offset:offset + schema_size]))
    offset += schema_size

    fields = schema["fields"]
    types = schema["types"]

    columns = {}

    # --- Lire les colonnes ---
    for field in fields:
        col_size = struct.unpack("I", data[offset:offset + 4])[0]
        offset += 4
        packed = c.decompress(data[offset:offset + col_size])
        offset += col_size

        col_type = types[field]

        if col_type == "int16":
            n = len(packed) // 2
            columns[field] = list(struct.unpack(f"{n}h", packed))

        elif col_type == "int32":
            n = len(packed) // 4
            columns[field] = list(struct.unpack(f"{n}i", packed))

        elif col_type == "float16":
            arr = np.frombuffer(packed, dtype=np.float16)
            columns[field] = arr.astype(np.float32).tolist()

        elif col_type == "float32":
            n = len(packed) // 4
            columns[field] = list(struct.unpack(f"{n}f", packed))

        elif col_type == "bool":
            columns[field] = [bool(b) for b in packed]

        else:
            columns[field] = orjson.loads(packed)

    # --- Lire les index (ignorés pour la reconstruction) ---
    num_indexes = struct.unpack("I", data[offset:offset + 4])[0]
    offset += 4

    for _ in range(num_indexes):
        name_len = struct.unpack("I", data[offset:offset + 4])[0]
        offset += 4 + name_len
        idx_size = struct.unpack("I", data[offset:offset + 4])[0]
        offset += 4 + idx_size

    # --- Reconstruire JSON ---
    num_rows = len(columns[fields[0]]) if fields else 0
    json_data = [
        {field: columns[field][i] for field in fields}
        for i in range(num_rows)
    ]

    return {
        "version": version,
        "fields": fields,
        "types": types,
        "num_rows": num_rows,
        "json_data": json_data
    }


class JONXFile:
    def __init__(self, path):
        self.path = path
        self.fields = []
        self.types = {}
        self.compressed_columns = {}
        self.indexes = {}
        self._load_file()

    def _load_file(self):
        with open(self.path, "rb") as f:
            data = f.read()

        result = decode_from_bytes(data)
        self.fields = result["fields"]
        self.types = result["types"]

        if not data.startswith(b"JONX"):
            raise ValueError("Le fichier n'est pas au format JONX")

        offset = 8

        schema_size = struct.unpack("I", data[offset:offset + 4])[0]
        offset += 4 + schema_size

        # --- Colonnes compressées ---
        for field in self.fields:
            col_size = struct.unpack("I", data[offset:offset + 4])[0]
            offset += 4
            self.compressed_columns[field] = data[offset:offset + col_size]
            offset += col_size

        # --- Index compressés ---
        num_indexes = struct.unpack("I", data[offset:offset + 4])[0]
        offset += 4

        for _ in range(num_indexes):
            name_len = struct.unpack("I", data[offset:offset + 4])[0]
            offset += 4
            name = data[offset:offset + name_len].decode()
            offset += name_len

            idx_size = struct.unpack("I", data[offset:offset + 4])[0]
            offset += 4
            self.indexes[name] = data[offset:offset + idx_size]
            offset += idx_size

    def _decompress_column(self, field_name, compressed):
        packed = zstd.ZstdDecompressor().decompress(compressed)
        t = self.types[field_name]

        if t == "int16":
            n = len(packed) // 2
            return list(struct.unpack(f"{n}h", packed))

        if t == "int32":
            n = len(packed) // 4
            return list(struct.unpack(f"{n}i", packed))

        if t == "float16":
            arr = np.frombuffer(packed, dtype=np.float16)
            return arr.astype(np.float32).tolist()

        if t == "float32":
            n = len(packed) // 4
            return list(struct.unpack(f"{n}f", packed))

        if t == "bool":
            return [bool(b) for b in packed]

        return orjson.loads(packed)

    def get_column(self, field_name):
        return self._decompress_column(field_name, self.compressed_columns[field_name])

    def find_min(self, field, column=None, use_index=False):
        if column is None:
            column = self.get_column(field)
        if use_index and field in self.indexes:
            idx = orjson.loads(zstd.ZstdDecompressor().decompress(self.indexes[field]))
            return column[idx[0]]
        return min(column)
