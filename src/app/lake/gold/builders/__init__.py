"""Gold builders — transforms silver into domain objects (feriados uses materializers/)."""

from app.lake.gold.builders import (
    bmf,
    cdi,
    ipca_dict,
    vna_lft,
)

BUILDER_MODULES = (
    cdi,
    bmf,
    ipca_dict,
    vna_lft,
)

__all__ = [
    "BUILDER_MODULES",
    "bmf",
    "cdi",
    "ipca_dict",
    "vna_lft",
]
