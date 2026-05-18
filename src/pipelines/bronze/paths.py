"""Hive-style paths under the bronze (raw) layer."""

from __future__ import annotations

from pathlib import Path

from config import get_settings


def get_bronze_root() -> Path:
    return get_settings().bronze_root


def bronze_dataset_dir(dataset: str) -> Path:
    return get_bronze_root() / dataset


def bronze_partition_dir(dataset: str, partition_key: str, value: str) -> Path:
    return bronze_dataset_dir(dataset) / f"{partition_key}={value}"


def bronze_partition_path(dataset: str, partition_key: str, value: str, ext: str) -> Path:
    """Full path to the artifact file inside a hive partition directory."""
    return bronze_partition_dir(dataset, partition_key, value) / f"part.{ext}"
