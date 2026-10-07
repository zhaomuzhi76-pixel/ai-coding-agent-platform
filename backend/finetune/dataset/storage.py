"""Compat shim. Original: storage.py.bak_autosplit."""
from ._storage_parts import *  # noqa
from ._storage_parts import (ensure_dataset_dir, _ensure_schema, dataset_file_path, dataset_file_exists, save_dataset_file, read_dataset_file, delete_dataset_file, save_dataset_metadata, update_dataset_metadata, load_dataset_metadata, list_dataset_metadata, delete_dataset_metadata, reset_dataset_metadata, DatasetStore)  # noqa
