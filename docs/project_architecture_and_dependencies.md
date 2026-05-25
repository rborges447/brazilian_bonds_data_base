# Arquitetura e dependências — Brazil Fixed Income Analytics

> **Documentação canônica** do código em `src/app/`. Referência por arquivo:
> [code_reference_for_ai.md](code_reference_for_ai.md).

## 1. Contexto

Data lake renda fixa Brasil: bronze → silver → gold → SQLite (futuro).

| Componente | Local |
|------------|-------|
| Aplicação | `src/app/` |
| Entry | `src/main.py`, `run_*.py` |
| Legado | `legacy/rf_lake/` |

## 2. Árvore `src/`

```
src/
  main.py
  app/
    cli/           bronze, silver, gold CLIs
    config/        settings, paths
    core/          dates, datasets, partitioning, exceptions
    contracts/     bronze, silver, provider protocols
    providers/     APIs externas
    lake/          bronze, silver, gold
    database/      connection, migrations (gold schema)
    repositories/  persistência gold SQLite
    services/      facades (ipca → lake builder)
    agents/        futuro
```

## 3. Fronteira de contratos

| Pacote | Conteúdo |
|--------|----------|
| `app/contracts/` | `ExtractResult`, `SilverTransform`, provider protocols |
| `app/lake/gold/contracts.py` | `BuilderName`, `BuilderContext`, `GoldMaterialized` |
| `app/core/` | calendário, datasets, particionamento |

## 4. Imports

`PYTHONPATH` = `src/`. Canônico: `from app.config import get_settings`, `from app.lake.gold import GoldOrchestrator`.

## 5. Entrypoints

- `python run_bronze.py` / `run_silver.py` / `run_gold.py`
- `python run_sync.py daily [YYYY-MM-DD] [--persist]` — bronze → silver → gold no intervalo `[DATA_START_DATE … fim]`
- `python run_sync.py status [YYYY-MM-DD]` — lacunas por camada (bronze/silver/gold)
- `rf-analytics bronze|silver|gold|sync|migrate` via `src/main.py`

### Sincronização diária

- **`DATA_START_DATE`** (`.env`): piso histórico; nenhuma camada processa datas anteriores.
- **`daily`** em cada camada (ou `run_sync.py daily`): reconcilia **todo** o intervalo até hoje, preenchendo só partições/linhas faltantes — não apenas o dia corrente.
- Ordem recomendada: bronze → silver → gold (`--persist` grava SQLite).
- Intervalo canônico: `app.core.sync_range` (`sync_start_date`, `sync_end_date`, `sync_business_days`, `sync_calendar_days`, `sync_months`, `sync_ipca_months`).
- **IPCA_DICT (gold):** uma linha por **dia civil** em `[DATA_START_DATE … hoje]`; bronze `ipca_indice` usa `sync_ipca_months` (4 meses antes do piso) para fechado M-1; CDI/PTAX/mercado seguem dias úteis.
- SIDRA IPCA: `SIDRA_DEFAULT_PERIOD` vazio → período automático de `sync_ipca_month_start()` até hoje.

## 6. Regras

- `app/providers` não importa `app/lake`
- `app/lake/silver` não importa providers
- `app/lake/gold` não importa providers
- `app/services` delega IPCA a `app.lake.gold.builders.ipca_dict` (sem duplicar regras)

## 7. Gold SQL

- DDL: [`src/app/database/migrations/`](src/app/database/migrations/)
- Documentação: [gold_schema_v2.md](gold_schema_v2.md)
- Sem tabelas gold `IPCA_INDICE` / `PROJECOES` — apenas `IPCA_DICT` diário + `CDI` + `PTAX`
- **Escrita:** `run_gold.py ... --persist` → `app.services.gold_persistence` → `app.repositories`
- **Leitura:** `app.database.queries` (SELECT `.sql`) + `app.database.readers.GoldReader`

```python
from app.database import GoldReader

reader = GoldReader()
reader.cdi.fetch_latest(10)
reader.cdi.fetch_on("2026-05-15")
reader.cdi.fetch_range("2026-01-01", "2026-05-22")
reader.mercado_com_liquidacoes.fetch_on("2026-05-15")  # full outer mercado + liquidações
```

## 8. Testes

`pytest tests/ -q`

Detalhe por módulo: [code_reference_for_ai.md](code_reference_for_ai.md).
