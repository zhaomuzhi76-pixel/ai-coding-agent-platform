"""Compat shim. Original: store.py.bak_autosplit."""
from ._store_parts import *  # noqa
from ._store_parts import (_ensure_schema, _case_to_dict, _dict_to_case, save_benchmark_result, load_benchmark_result, list_benchmark_runs, latest_benchmark_for, delete_benchmark_run, reset_benchmark_runs, BenchmarkStore)  # noqa
