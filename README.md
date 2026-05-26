# Brazilian Bonds DB (`brazilian_bonds_db`)

Pacote Python de **base de dados local** para séries e tabelas de renda fixa brasileira (CDI, PTAX, IPCA, mercado secundário, leilões, BMF, etc.). Instale o pacote, atualize os dados com `update()` e consulte tudo via `read_data()`.

**API pública:** apenas `update()` e `read_data()`. Não é necessário importar `GoldReader`, SQL ou módulos do lake.

> **Clone:** substitua `SEU_ORG/SEU_REPO` pela URL real do repositório no GitHub (seções abaixo).

---

## Requisitos

- Python **3.10+**
- Git
- Credenciais/configuração para fontes usadas no sync (ver [Configuração](#configuração))

---

## Instalação a partir do GitHub

### 1. Clonar o repositório

```powershell
git clone https://github.com/SEU_ORG/SEU_REPO.git
cd SEU_REPO
```

### 2. Ambiente virtual

```powershell
python -m venv venv
.\venv\Scripts\activate   # Windows
# source venv/bin/activate   # Linux/macOS
```

### 3. Instalar o pacote (modo editável)

No diretório raiz do clone:

```powershell
pip install -e .
```

Para desenvolver ou rodar testes neste repositório:

```powershell
pip install -e ".[dev]"
```

Verifique o import:

```powershell
python -c "import brazilian_bonds_db as bbdb; print(bbdb.update, bbdb.read_data)"
```

### 4. Instalar em outro projeto

Com o repositório clonado em disco:

```powershell
pip install -e "C:\caminho\para\brazil_fixed_income_analytics"
```

Quando houver URL publicada no GitHub:

```powershell
pip install git+https://github.com/SEU_ORG/SEU_REPO.git@main
```

---

## Configuração

O `update()` baixa e processa dados de provedores (ANBIMA, BCB, Tesouro, SIDRA, etc.). Copie o exemplo de variáveis de ambiente:

```powershell
copy .env.example .env
```

Edite `.env` no diretório de trabalho (projeto consumidor ou raiz do clone) com pelo menos:

| Variável | Uso |
|----------|-----|
| `ANBIMA_CLIENT_ID` / `ANBIMA_CLIENT_SECRET` | Mercado secundário, projeções |
| `DATA_START_DATE` | Início do histórico no sync (ex. `2026-01-01`) |
| `BCB_*`, `TESOURO_*`, `FERIADOS_*` | URLs/timeouts (defaults costumam bastar) |
| `UPTODATA_*` | Ajustes BMF (opcional; arquivos locais B3) |

Lista completa: [`.env.example`](.env.example).

---

## Onde os dados ficam

Com `update()` / `read_data()` e layout de **pacote**, o padrão é:

```text
./data/brazilian_bonds_db/
  database/app.db            # SQLite (tabelas gold)
  lake/bronze|silver|gold    # arquivos internos do pipeline
  logs/
  metadata/
```

Caminho customizado:

```python
bbdb.update(data_root="D:/dados/bonds_db")
data = bbdb.read_data(data_root="D:/dados/bonds_db")
```

---

## Uso básico

```python
import brazilian_bonds_db as bbdb

# 1) Criar/atualizar base local (migrations + sync se necessário)
result = bbdb.update()

# 2) Ler dados curados (um atributo por dataset)
data = bbdb.read_data()

df_cdi = data.cdi.fetch_latest(10)
df_ptax = data.ptax.fetch_range("2025-01-01", "2025-12-31")
```

Import alternativo:

```python
from brazilian_bonds_db import read_data

data = read_data()
```

---

## `update()` — parâmetros úteis

```python
bbdb.update(
    data_root=None,      # default: ./data/brazilian_bonds_db
    datasets=None,       # lista restrita; None = todos
    start_date=None,     # YYYY-MM-DD
    end_date=None,
    force=False,         # False: incremental. True: refresh destrutivo no escopo.
    persist=True,        # persiste bronze/silver/gold
    refresh_dates=None, # list[str] (ISO). Usado apenas com force=True.
)
```

Fluxo automático: pastas → migrations SQLite → detectar lacunas → sync bronze → silver → gold.

---

## Refresh destrutivo (`force=True`)

Quando `force=True`, o `update()` **apaga e reprocessa** bronze, silver e gold **no escopo** (`datasets` + janela de datas), **antes** do sync (em vez de apenas rodar incremental).

### `force=False` (padrão)

Comportamento incremental: o sync roda apenas onde há lacunas obrigatórias (bronze/silver/gold faltando).

### `force=True`

- Se `datasets=None`, o escopo inclui **todos** os datasets do pipeline.
- Se `datasets=[...]`, o escopo é restrito aos datasets informados.
- Se `refresh_dates=[\"YYYY-MM-DD\", ...]`, a invalidação diária fica limitada às datas explícitas dentro de `start_date`…`end_date`.

Tabela compacta (datasets → gold/table):

| Dataset | Gold / tabela | Granularidade |
|---------|---------------|---------------|
| `cdi` | `CDI` | dia |
| `ptax` | `PTAX` | dia |
| `mercado_secundario` | `MERCADO_SECUNDARIO` | dia |
| `liquidacoes_mercado` | `LIQUIDACOES_MERCADO` | dia |
| `leiloes` | `LEILOES` | dia |
| `ajustes_bmf` | `AJUSTES_BMF` | dia |
| `ipca_indice`, `projecoes` | `IPCA_DICT` | mês → série diária |
| `feriados` | `FERIADOS` | snapshot |

### Nota especial: `ipca_dict` (IPCA mensal)

Quando o escopo de `force=True` invalidar um mês de `ipca_indice` e/ou `projecoes`, o pipeline rematerializa a **série diária** de `IPCA_DICT` a partir do primeiro dia do mês impactado **até a data final do sync** (lógica existente do builder `ipca_dict`).

### Exemplos

Caso motivador (`ajustes_bmf` com data única):

```python
import brazilian_bonds_db as bbdb

bbdb.update(
    data_root="./data/brazilian_bonds_db",
    datasets=["ajustes_bmf"],
    start_date="2026-05-25",
    end_date="2026-05-25",
    force=True,
    refresh_dates=["2026-05-25"],
)

data = bbdb.read_data(data_root="./data/brazilian_bonds_db")
df = data.ajustes_bmf.fetch_on("2026-05-25")
```

Janela ampla (`datasets=None`):

```python
bbdb.update(
    data_root="./data/brazilian_bonds_db",
    start_date="2026-05-01",
    end_date="2026-05-31",
    force=True,
)
```

Aviso: operação mais pesada. Se souber o conjunto de datasets e datas a corrigir, prefira `datasets` + `refresh_dates`.

---

## `read_data()` — datasets

O objeto retornado expõe atributos por dataset. Métodos comuns: `fetch_all()`, `fetch_latest(n)`, `fetch_on(date)`, `fetch_range(start, end)` (nem todo dataset suporta todos).

**Séries diárias:** `cdi`, `ptax`, `ipca_dict`, `mercado_secundario`, `liquidacoes_mercado`, `leiloes`, `ajustes_bmf` — `fetch_latest(n)` retorna todas as linhas das últimas **n datas** distintas (não as últimas n linhas).

**Snapshot (`fetch_all` apenas):** `feriados`, `titulos_publicos`, `contratos_bmf`

**Combinado:** `mercado_com_liquidacoes` (alias `mercado_liquidacoes`)

Referência completa: [`docs/gold_reader_public_api.md`](docs/gold_reader_public_api.md)

```python
data = bbdb.read_data(db_path="/caminho/app.db")
data = bbdb.read_data(data_root="./data/brazilian_bonds_db")
```

---

## Exemplo completo

```python
import brazilian_bonds_db as bbdb

bbdb.update(data_root="./data/brazilian_bonds_db")
data = bbdb.read_data(data_root="./data/brazilian_bonds_db")

print(data.cdi.fetch_latest(5))
print(data.titulos_publicos.fetch_all().head())
```

---

## Solução de problemas

| Problema | O que verificar |
|----------|-----------------|
| `ModuleNotFoundError: brazilian_bonds_db` | `pip install -e .` no repo correto; venv ativo |
| Sync falha ANBIMA | `ANBIMA_CLIENT_ID` / `SECRET` no `.env` |
| Banco vazio após `read_data` | Executar `update()` antes; conferir `result.db_path` |
| Dados desatualizados / incompletos | `bbdb.update(force=True, datasets=[...], refresh_dates=[...])` ou ajuste `start_date` / `end_date` |
| Layout dev vs pacote | CLI do repo usa `data/app.db`; consumidor usa `data/brazilian_bonds_db` |

---

## O que este pacote não é

- Não é API HTTP nem dashboard.
- Não é motor de precificação de títulos (foco em **dados** curados).
- Consumidor não deve usar `from app.lake import ...` nem `GoldReader` por nome.

---

## Desenvolvimento do repositório

Para bronze/silver/gold, CLI e layout **dev** (`data/app.db`), veja [docs/development.md](docs/development.md) (documentação de mantenedores; em atualização na Feature 003).

CLI dev de sync incremental: `python run_sync.py daily [YYYY-MM-DD] [--persist]`. Para refresh destrutivo no layout local (mesma semântica de `update(force=True)` em `data/app.db`), use `python run_sync.py daily --force [--start-date ...] [--datasets ...] [--refresh-dates ...]`. Consumidores externos devem usar `bbdb.update()`, não a CLI.

Outros documentos:

- [docs/gold_schema_v2.md](docs/gold_schema_v2.md)
- [docs/project_architecture_and_dependencies.md](docs/project_architecture_and_dependencies.md)

```powershell
pip install -e ".[dev]"
pytest tests/public/ -q
```
