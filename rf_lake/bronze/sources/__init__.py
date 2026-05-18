"""
External data sources module: HTTP clients for external APIs.

This module contains clients to fetch raw data from external sources:
- ANBIMA (secondary market, projections, auctions)
- BCB (market settlements)
- Treasury Direct — Brazilian government's retail bond auctions channel
- UpToData (BMF adjustments)
- Sidra/IBGE (IPCA)

Responsibilities:
- Authenticate with external APIs when required
- Fetch raw data (HTTP requests)
- Basic mapping from API response → DataFrame
- Raw data validation

Allowed dependencies:
- settings (credentials, timeouts)
- logging
- Standard library and third-party libs (requests, pandas)

Forbidden dependencies:
- db/ (must not depend on persistence)
- etl/ (must not depend on pipelines)
- jobs/ (must not depend on orchestration)
- export/ (must not depend on export)
"""

from rf_lake.bronze.sources.anbima.client import AnbimaClient

__all__ = ["AnbimaClient"]
