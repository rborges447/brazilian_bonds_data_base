# Brazil Fixed Income Analytics

Refatoração em andamento. Código legado em [`legacy/`](legacy/).

## Estrutura (`src/app/`)

```
src/
  main.py              # rf-analytics bronze|silver|gold|migrate
  app/
    cli/               # entrypoints bronze, silver, gold
    config/            # settings, paths
    core/              # dates, datasets, partitioning
    contracts/         # DTOs e protocols
    providers/         # ANBIMA, BCB, Tesouro, SIDRA, feriados, UpToData
    lake/
      bronze/          # ingestão raw
      silver/          # normalização Parquet
      gold/            # materialização analítica
    database/          # SQLite migrations
    repositories/      # persistência gold
    services/          # facades (sem lógica IPCA duplicada)
```

## Configuração

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
```

Variáveis: `DATA_ROOT`, `SQLITE_DB_PATH`, `DATA_START_DATE`, `ANBIMA_*`, `BCB_*`, etc. — ver [`.env.example`](.env.example).

```python
from app.config import get_settings
from app import get_settings  # atalho
```

## Rodar pipelines

### Bronze

```powershell
python run_bronze.py init
python run_bronze.py daily
python run_bronze.py one cdi 2026-05-15
python run_bronze.py backfill 2026-01-01 2026-05-15 mercado_secundario
```

### Silver

```powershell
python run_silver.py init
python run_silver.py daily
python run_silver.py one cdi 2026-05-15
python run_silver.py backfill 2026-01-01 2026-05-15
```

### Gold (materialização + SQLite schema v2)

```powershell
python run_gold.py migrate
python run_gold.py one feriados --persist
python run_gold.py one cdi 2026-05-15 --persist
python run_gold.py one ipca_dict 2026-05-15 --persist
python run_gold.py backfill 2026-05-01 2026-05-15 ipca_dict --persist
```

Gold schema: [`docs/gold_schema_v2.md`](docs/gold_schema_v2.md). Migrations em `src/app/database/migrations/`. Apague `data/app.db` antes de `migrate` se o arquivo for de um schema antigo.

### Dispatcher unificado

```powershell
rf-analytics bronze init
rf-analytics silver daily
rf-analytics gold one ipca_dict 2026-05-15
rf-analytics migrate
```

## Testes

```powershell
pytest tests/ -q
```

## Documentação

- [docs/project_architecture_and_dependencies.md](docs/project_architecture_and_dependencies.md)
- [docs/gold_schema_v2.md](docs/gold_schema_v2.md)
- [docs/code_reference_for_ai.md](docs/code_reference_for_ai.md)
- Regenerar: `python docs/_build_docs.py`

## Legado

```powershell
cd legacy
pip install -e ".[dev]"
python run_lake.py migrate
```
