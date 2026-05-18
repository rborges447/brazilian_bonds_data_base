# Brazil Fixed Income Analytics (legado)

> Código preservado na refatoração. Instale com `pip install -e ".[dev]"` **a partir desta pasta** (`legacy/`).

Brazilian fixed-income data lake (`rf_lake`) with layered ingestion (Bronze → Silver → Gold in SQLite) and a `Database` read facade for notebooks and a future HTTP API.

## Requirements

- Python 3.10+
- [ANBIMA](https://www.anbima.com.br/) API credentials (required for `mercado_secundario` and `projecoes` pipelines)
- Public sources: BCB, Tesouro Nacional, SIDRA/IBGE (no extra credentials in `.env.example`)

### UpToData (BMF adjustments) — optional, not in `.env.example`

The `ajustes_bmf` pipeline reads settlement files from **[UpToData](https://www.uptodata.com.br/)**, a **paid B3 market data service**. It is not part of the public template because access is licensed per desk and paths are deployment-specific.

If you have a subscription, add these variables to your **local** `.env` (never commit them):

```bash
UPTODATA_PASTA_INTEREST_RATE_BASE=/path/to/Interest_Rate/SettlementPrice
UPTODATA_ARQUIVO_INTEREST_RATE_BASE=Interest_Rate_SettlementPriceFile_Futures_
```

Without UpToData, other datasets still run; only `ajustes_bmf` is affected.

## Quick start

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
# source venv/bin/activate

pip install -e ".[dev]"
copy .env.example .env   # Windows — fill in credentials
# cp .env.example .env   # Linux/macOS

python run_lake.py migrate
pytest tests/ -q
```

## Environment variables

Copy [`.env.example`](.env.example) to `.env` and set values.

| Variable | Description |
|----------|-------------|
| `DATA_START_DATE` | Default start date for incremental backfill (`YYYY-MM-DD`) |
| `SQLITE_DB_PATH` | Gold SQLite path (e.g. `data/app.db`) |
| `ANBIMA_CLIENT_ID` / `ANBIMA_CLIENT_SECRET` | ANBIMA OAuth2 |
| `ANBIMA_TIMEOUT` / `ANBIMA_MAX_RETRIES` | ANBIMA HTTP client |
| `BCB_*` / `TESOURO_*` | Timeouts and retries for BCB and Tesouro APIs |
| `LOG_LEVEL` | Log level (`INFO`, `DEBUG`, …) |

**Never commit `.env`** — it holds secrets and is listed in `.gitignore`.

## Architecture

```
rf_lake/
  bronze/          # extract (HTTP / files → Parquet/JSON under data/raw)
  silver/          # normalize
  gold/            # SQLite persistence + SQL queries
  jobs/            # daily, backfill, run_one
  data_reader/     # Database facade (product / future HTTP API)
data/              # local artifacts (gitignored)
```

| Layer | Role |
|-------|------|
| **Bronze** | Raw pulls from ANBIMA, BCB, Tesouro, SIDRA; optional UpToData files for BMF |
| **Silver** | Typed Parquet, rename maps aligned with Gold schema |
| **Gold** | SQLite (`app.db`), versioned migrations, `get_*` queries |
| **data_reader** | `Database` class — single entry for external consumers |

- **Internal pipeline:** jobs and `rf_lake` modules import `gold.db.queries` and layer runners directly.
- **External use:** `from rf_lake.data_reader import Database` (notebooks, future FastAPI).

## Data sources (summary)

| Dataset | Source | Auth in `.env.example` |
|---------|--------|-------------------------|
| `mercado_secundario`, `projecoes`, `leiloes`, `feriados` | ANBIMA API | Yes |
| `liquidacoes_mercado` | BCB | Timeouts only |
| `leiloes` (Tesouro) | Tesouro Nacional | Timeouts only |
| `ipca_indice` | SIDRA (IBGE) | No |
| `ajustes_bmf` | UpToData (B3, paid) | Local `.env` only |

## CLI

```bash
python run_lake.py migrate
python run_lake.py daily [YYYY-MM-DD]
python run_lake.py backfill START_DATE END_DATE [PIPELINE]
python run_lake.py one PIPELINE DATE
```

After `pip install -e .`:

- `rf-lake-migrate`
- `rf-lake-daily`

## Tests

```bash
pytest tests/ -q
```

Tests marked `integration` need a populated local `data/` directory.

## Publishing to GitHub

Public repo: code, `.env.example`, docs, and CI only — no secrets or local databases.

### Pre-push checklist

- [ ] `.env` is not staged (`git status` must not list it)
- [ ] `.env.example` uses placeholders only (`your_client_id`)
- [ ] `data/`, `venv/`, `*.db`, `.cursor/` are ignored
- [ ] If `.env` was committed by mistake: `git rm --cached .env` and rotate ANBIMA credentials

### First push

```bash
git remote add origin https://github.com/<org>/<repo>.git
git push -u origin main
```

Create the GitHub repository as **Public** without an initial README (this repo already includes one).

## License

MIT — see [LICENSE](LICENSE).
