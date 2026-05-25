"""Market data facade (placeholder for CDI, PTAX, etc. via gold)."""

from __future__ import annotations

from app.lake.gold import GoldOrchestrator


def get_orchestrator() -> GoldOrchestrator:
    """Return a stateless gold orchestrator for batch materialization."""
    return GoldOrchestrator()
