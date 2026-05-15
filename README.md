# Brazil Fixed Income Analytics

Data lake e camada de leitura para analytics de renda fixa no Brasil (`rf_lake`): ingestão em camadas Bronze → Silver → Gold (SQLite), com fachada `Database` para consumo por API e notebooks.

## Requisitos

- Python 3.10+
- Credenciais ANBIMA (para pipelines `mercado_secundario` e `projecoes`)
- Opcional: acesso a arquivos UpToData (ajustes BMF) conforme paths no `.env`

## Setup rápido

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
# source venv/bin/activate

pip install -e ".[dev]"
copy .env.example .env   # Windows — preencha credenciais
# cp .env.example .env   # Linux/macOS

python run_lake.py migrate
pytest tests/ -q
```

## Variáveis de ambiente

Copie [`.env.example`](.env.example) para `.env` e ajuste os valores.

| Variável | Descrição |
|----------|-----------|
| `DATA_START_DATE` | Data inicial padrão para backfill incremental |
| `SQLITE_DB_PATH` | Caminho do SQLite Gold (ex.: `data/app.db`) |
| `ANBIMA_CLIENT_ID` / `ANBIMA_CLIENT_SECRET` | OAuth ANBIMA |
| `ANBIMA_TIMEOUT` / `ANBIMA_MAX_RETRIES` | HTTP ANBIMA |
| `BCB_*` / `TESOURO_*` | Timeouts e retries BCB / Tesouro |
| `UPTODATA_PASTA_*` / `UPTODATA_ARQUIVO_*` | Paths UpToData (ajustes BMF) |
| `LOG_LEVEL` | Nível de log (`INFO`, `DEBUG`, …) |

**Nunca commite o arquivo `.env`** — ele contém segredos e está no `.gitignore`.

## Arquitetura

```
rf_lake/
  bronze/          # extração (APIs / arquivos → Parquet/JSON em data/raw)
  silver/          # normalização
  gold/            # persistência SQLite + queries SQL
  jobs/            # daily, backfill, run_one
  data_reader/     # fachada Database (produto / futura API HTTP)
data/              # dados locais (ignorado pelo Git)
```

- **Pipeline interno:** jobs e módulos em `rf_lake` importam `gold.db.queries` e camadas Bronze/Silver/Gold diretamente.
- **Consumo externo:** use `from rf_lake.data_reader import Database` (notebooks, futura API FastAPI).

## CLI

```bash
python run_lake.py migrate
python run_lake.py daily [YYYY-MM-DD]
python run_lake.py backfill START_DATE END_DATE [PIPELINE]
python run_lake.py one PIPELINE DATE
```

Entry points instaláveis (após `pip install -e .`):

- `rf-lake-migrate`
- `rf-lake-daily`

## Testes

```bash
pytest tests/ -q
```

Testes marcados com `integration` exigem `data/` populado localmente.

## Publicar no GitHub

Repositório **público**: apenas código, `.env.example`, documentação e CI. Dados e segredos ficam fora do Git.

### Checklist antes do push

- [ ] `.env` não está no staging (`git status` não deve listá-lo)
- [ ] `.env.example` usa placeholders (`your_client_id`), sem credenciais reais
- [ ] Pastas `data/`, `venv/`, `*.db`, `.cursor/` ignoradas
- [ ] Se `.env` já foi commitado por engano: `git rm --cached .env` e rotacione credenciais ANBIMA

### Primeiro push

```bash
git init
git add .
git status   # revisar lista de arquivos
git commit -m "Initial commit: rf_lake data platform and MIT license"
git branch -M main
git remote add origin https://github.com/<org>/<repo>.git
git push -u origin main
```

Crie o repositório no GitHub como **Public**, **sem** README inicial (este projeto já inclui um).

## Licença

MIT — ver [LICENSE](LICENSE).
