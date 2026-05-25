# Gold SQL schema

Canonical DDL: [`src/app/database/migrations/`](../src/app/database/migrations/).

## Silver vs gold

| Layer | IPCA |
|-------|------|
| Silver (Parquet) | `ipca_indice` (monthly), `projecoes` (monthly JSON) |
| Gold (SQLite) | **`IPCA_DICT` only** — one row per business day |

## Tables and relationships

### Independent (no FK)

| Table | PK | Builder |
|-------|-----|---------|
| `FERIADOS` | `data` | `feriados` |
| `CDI` | `data_referencia` | `cdi` |
| `PTAX` | `data_referencia` | `ptax` |
| `IPCA_DICT` | `data_referencia` | `ipca_dict` |

### Títulos públicos cluster

| Table | PK | FK |
|-------|-----|-----|
| `TITULOS_PUBLICOS` | `(tipo_titulo, data_vencimento)` | — |
| `MERCADO_SECUNDARIO` | `(tipo_titulo, data_vencimento, data_referencia)` | → `TITULOS_PUBLICOS` |
| `LIQUIDACOES_MERCADO` | `(tipo_titulo, data_vencimento, data_referencia)` | → `TITULOS_PUBLICOS` |
| `LEILOES` | `(tipo_titulo, data_vencimento, data_referencia, numero_edital)` | → `TITULOS_PUBLICOS` |

### BMF

| Table | PK | FK |
|-------|-----|-----|
| `CONTRATOS_BMF` | `ticker` | — |
| `AJUSTES_BMF` | `(ticker, data_referencia)` | → `CONTRATOS_BMF` |

### Operational

| Table | Purpose |
|-------|---------|
| `schema_migrations` | Applied migration versions |
| `job_runs` | Pipeline audit (future use) |

## Apply migrations

```python
from app.database import apply_migrations
apply_migrations()
```

Or: `python run_gold.py migrate` / `rf-analytics migrate`.

**Dev:** delete `data/app.db` and re-run migrate when changing DDL.

## Persist gold output

```bash
python run_gold.py one cdi 2026-05-15 --persist
```

Flow: `GoldOrchestrator` → `GoldMaterialized` → `app.services.gold_persistence` → repositories.

## PostgreSQL (future)

DDL avoids `WITHOUT ROWID`. Dates are `TEXT` ISO `YYYY-MM-DD` (migrate to `DATE` in PG). Booleans use `INTEGER 0/1` (`usa_fechado`). Upserts live in repositories (`INSERT OR REPLACE` today; `ON CONFLICT` for PG). See `app.database.connection.Dialect` and `app.database.sql.upsert_prefix`.
