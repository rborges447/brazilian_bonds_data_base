"""Import alias package for external consumers."""

from __future__ import annotations

from .readers import read_data
from .update import update

__all__ = ["read_data", "update"]
