# Rascunho — README para consumidor do pacote

> Conteúdo aplicado em `README.md` (Task 003 / Task 5). Manter este arquivo como referência ou apagar depois.
> Substituir `SEU_ORG/SEU_REPO` no README pela URL real do GitHub quando disponível.

---

# Brazilian Bonds DB (`brazilian_bonds_db`)

Pacote Python de **base de dados local** para séries e tabelas de renda fixa brasileira (CDI, PTAX, IPCA, mercado secundário, leilões, BMF, etc.). Você instala o pacote no seu projeto, atualiza os dados com `update()` e consulta tudo via `read_data()` — sem montar pipeline bronze/silver/gold manualmente.

**API pública:** apenas `update()` e `read_data()`. Não é necessário importar `GoldReader`, SQL ou módulos do lake.

---

## Requisitos

- Python **3.10+**
- Git
- Credenciais/configuração para fontes externas usadas no sync (ver [Configuração](#configuração))

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

Para desenvolver/testar o próprio repositório:

```powershell
pip install -e ".[dev]"
```

Verifique o import:

```powershell
python -c "import brazilian_bonds_db as bbdb; print(bbdb.update, bbdb.read_data)"
```

### 4. Instalar em *outro* projeto (sem clonar para trabalhar no código)

Ainda é necessário um checkout ou artefato instalável:

```powershell
pip install -e "Z:\caminho\para\brazil_fixed_income_analytics"
# ou, quando houver release no GitHub:
# pip install git+https://github.com/SEU_ORG/SEU_REPO.git@main
```

---

## Configuração

O `update()` baixa e processa dados de provedores (ANBIMA, BCB, Tesouro, SIDRA, etc.). Copie o exemplo de variáveis de ambiente:

```powershell
copy .env.example .env
```

Edite `.env` no **seu projeto consumidor** (ou no diretório de trabalho atual) com pelo menos:

| Variável | Uso |
|----------|-----|
| `ANBIMA_CLIENT_ID` / `ANBIMA_CLIENT_SECRET` | Mercado secundário, projeções |
| `DATA_START_DATE` | Início do histórico no sync (ex. `2026-01-01`) |
| `BCB_*`, `TESOURO_*`, `FERIADOS_*` | URLs/timeouts (defaults costumam bastar) |
| `UPTODATA_*` | Ajustes BMF (opcional; paths locais B3) |

Detalhes: arquivo [`.env.example`](../.env.example) na raiz do repositório instalado.

---

## Onde os dados ficam

Por padrão, ao usar `update()` / `read_data()` com `data_root`, o pacote usa o layout:

```text
./data/brazilian_bonds_db/
  database/app.db          # SQLite (tabelas gold)
  lake/bronze|silver|gold  # arquivos internos do pipeline
  logs/
  metadata/
```

Você pode passar outro caminho:

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
# result.skipped_sync, result.db_path, etc. — relatório estruturado

# 2) Ler dados curados (objeto com um atributo por dataset)
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
    data_root=None,           # pasta do pacote; default ./data/brazilian_bonds_db
    datasets=None,            # lista restrita de datasets; None = todos
    start_date=None,          # YYYY-MM-DD
    end_date=None,
    force=False,              # True força sync mesmo sem gaps
    persist=True,             # persiste bronze/silver/gold
)
```

Fluxo interno (você não precisa chamar à mão): garantir pastas → migrations SQLite → detectar lacunas → sync bronze → silver → gold.

---

## `read_data()` — datasets e métodos

O objeto retornado expõe **atributos por dataset**. Métodos típicos (nem todo dataset tem todos):

| Método | Descrição |
|--------|-----------|
| `fetch_all()` | Série/tabela completa |
| `fetch_latest(n)` | Últimas `n` linhas/datas |
| `fetch_on(date)` | Um dia (`YYYY-MM-DD`) |
| `fetch_range(start, end)` | Intervalo |

### Séries diárias

- `data.cdi`
- `data.ptax`
- `data.ipca_dict`
- `data.mercado_secundario`
- `data.liquidacoes_mercado`
- `data.leiloes`
- `data.ajustes_bmf`
- `data.feriados`

### Tabelas de dimensão (`fetch_all`, `fetch_latest`)

- `data.titulos_publicos`
- `data.contratos_bmf`

### View combinada

- `data.mercado_com_liquidacoes` (alias `data.mercado_liquidacoes`)

Documentação detalhada: [`docs/gold_reader_public_api.md`](gold_reader_public_api.md) (a ser gerada na Feature 003).

### Caminhos explícitos

```python
# Banco em arquivo específico
data = bbdb.read_data(db_path="/caminho/app.db")

# Layout pacote em pasta customizada
data = bbdb.read_data(data_root="./data/brazilian_bonds_db")
```

---

## Exemplo completo (novo projeto)

```python
import brazilian_bonds_db as bbdb

bbdb.update(data_root="./data/brazilian_bonds_db", force=False)

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
| Banco vazio após `read_data` | Rodar `update()` antes; conferir `result.db_path` |
| Dados antigos | `bbdb.update(force=True)` ou ajustar `start_date` / `end_date` |
| Uso no repo de desenvolvimento | CLI `run_sync.py` usa layout **dev** (`data/app.db`); consumidor usa **pacote** (`data/brazilian_bonds_db`) |

---

## O que este pacote *não* é

- Não é API HTTP nem dashboard.
- Não expõe fórmulas de precificação de títulos (foco: **dados** curados).
- Consumidor **não** deve depender de `from app.lake import ...` ou `GoldReader` por nome.

---

## Desenvolvimento do repositório (mantenedores)

Se você altera o código em `src/app/` (bronze/silver/gold, CLI):

- Layout dev: `DATA_ROOT=data`, `SQLITE_DB_PATH=data/app.db`
- Scripts: `run_sync.py`, `run_bronze.py`, `run_silver.py`, `run_gold.py`
- Documentação interna: [`docs/project_architecture_and_dependencies.md`](project_architecture_and_dependencies.md)

```powershell
pip install -e ".[dev]"
pytest tests/public/ -q
```

---

## Licença / suporte

_(Preencher conforme política do repositório.)_
