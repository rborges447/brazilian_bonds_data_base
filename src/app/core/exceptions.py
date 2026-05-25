"""Shared pipeline exceptions (not layer contracts)."""

from __future__ import annotations


class PipelineError(Exception):
    """Base error for lake pipeline operations."""


class DatasetNotFoundError(PipelineError):
    """Unknown or unregistered dataset name."""


class PartitionMissingError(PipelineError):
    """Expected partition artifact is absent on disk."""
