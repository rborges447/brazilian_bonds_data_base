"""Public read alias (delegates to app.public)."""

from __future__ import annotations

from app.public.readers import read_data

__all__ = ["read_data"]
