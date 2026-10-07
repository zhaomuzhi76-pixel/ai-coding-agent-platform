"""Part 2 of storage.py."""
from ._header import Any, DATASET_DIR_NAME, DATASET_ID_PREFIX, DatasetFormat, DatasetSpec, Path, _DATASET_DIR, _DB_DIR, _DB_PATH, annotations, json, sqlite3, time

class DatasetStore:
    VERSION = "1.0"
    def save_file(self, did, content): return save_dataset_file(did, content)
    def read_file(self, did): return read_dataset_file(did)
    def delete_file(self, did): return delete_dataset_file(did)
    def file_exists(self, did): return dataset_file_exists(did)
    def file_path(self, did): return str(dataset_file_path(did))
    def save_meta(self, spec): save_dataset_metadata(spec)
    def load_meta(self, did): return load_dataset_metadata(did)
    def list_meta(self, limit=100): return list_dataset_metadata(limit=limit)
    def delete_meta(self, did): return delete_dataset_metadata(did)
    def reset(self): reset_dataset_metadata()
    def ready(self): return True
    def dump(self):
        return {"name": type(self).__name__, "version": self.VERSION}

