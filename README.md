# Brazil Fixed Income Analytics

Refatoração em andamento. O código anterior (`rf_lake`, jobs, testes antigos) está em [`legacy/`](legacy/).

## Estrutura nova

```
src/
  config/          # configuração e settings
  database/        # conexões e sessões
  models/          # modelos de domínio
  contracts/       # interfaces e DTOs
  providers/       # fontes externas (APIs, arquivos)
  repositories/    # persistência
  pipelines/
    bronze/        # ingestão bruta
    silver/        # normalização
    gold/          # camada analítica / persistência final
  agents/          # agentes (futuro)
  services/        # orquestração e casos de uso
  main.py          # entry point
tests/
migrations/
```

## Configuração

Copie [`.env.example`](.env.example) para `.env` na raiz do repositório. Variáveis agrupadas por fonte:

- **Paths:** `DATA_ROOT`, `SQLITE_DB_PATH`, `DATA_START_DATE`
- **ANBIMA API:** `ANBIMA_CLIENT_ID`, `ANBIMA_CLIENT_SECRET`, …
- **Feriados (XLS público):** `FERIADOS_XLS_URL`, `FERIADOS_TIMEOUT`
- **BCB / Tesouro / SIDRA / UpToData:** prefixos `BCB_`, `TESOURO_`, `SIDRA_`, `UPTODATA_`

Uso em código: `from config import get_settings` → `get_settings().anbima`, `.paths`, `.db_path`, etc.

## Providers

Clientes por fonte em `src/providers/` (`anbima`, `feriados`, `bcb`, `tesouro`, `sidra`, `uptodata`). Cada um recebe sub-settings via `get_settings()` ou injeção explícita.

UpToData exige `UPTODATA_PASTA_INTEREST_RATE_BASE` e `UPTODATA_ARQUIVO_INTEREST_RATE_BASE` no `.env` local para ajustes BMF.

## Rodar bronze (camada raw, partições Hive)

```bash
pip install -e ".[dev]"
python run_bronze.py init
python run_bronze.py daily              # até hoje, incremental por partição
python run_bronze.py daily 2026-01-17
python run_bronze.py one feriados
python run_bronze.py one liquidacoes_mercado 2026-01-15
python run_bronze.py one cdi 2026-01-15
python run_bronze.py one ptax 2026-01-15
python run_bronze.py backfill 2026-01-01 2026-01-17
python run_bronze.py backfill 2026-01-01 2026-01-17 mercado_secundario
```

Artefatos em `data/raw/{dataset}/{partition_key}={value}/part.{json|parquet}`.

**Projeções ANBIMA (`projecoes`):** partições por `mes_referencia` (não pelo mês da consulta API). O `daily` re-pulla mês anterior, corrente e seguinte; novas coletas (`data_coleta`) são mescladas no JSON bronze sem apagar histórico.

## Rodar silver (normalização canônica)

```bash
python run_silver.py init
python run_silver.py daily
python run_silver.py one cdi 2026-01-15
python run_silver.py backfill 2026-01-01 2026-01-17 mercado_secundario
```

Artefatos em `data/silver/{dataset}/{partition_key}={value}/part.parquet`.  
Partições mensais (`ipca_indice`, `projecoes`) permanecem mensais no disco; use `pipelines.silver.expand.read_monthly_as_daily` para expandir a dias úteis na leitura.

## Quick start

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -e ".[dev]"
copy .env.example .env         # ajuste variáveis locais
pytest tests/ -q
```

## Código legado

Para rodar o data lake antigo:

```bash
cd legacy
pip install -e ".[dev]"
python run_lake.py migrate
```

Documentação completa do lake antigo: [`legacy/README.md`](legacy/README.md).
