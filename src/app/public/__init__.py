"""Stable public facade over internal app implementation."""

from app.public.readers import read_data
from app.public.update import update

__all__ = ["read_data", "update"]
