"""Hive-style paths under the silver layer."""

from __future__ import annotations

from pathlib import Path

from config import get_settings


def get_silver_root() -> Path:
    return get_settings().silver_root


def silver_dataset_dir(dataset: str) -> Path:
    return get_silver_root() / dataset


def silver_partition_dir(dataset: str, partition_key: str, value: str) -> Path:
    return silver_dataset_dir(dataset) / f"{partition_key}={value}"


def silver_partition_path(dataset: str, partition_key: str, value: str, ext: str = "parquet") -> Path:
    """Full path to the artifact file inside a hive partition directory."""
    return silver_partition_dir(dataset, partition_key, value) / f"part.{ext}"
