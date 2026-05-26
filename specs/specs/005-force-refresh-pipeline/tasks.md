# Tasks — 005 `force` refresh destrutivo bronze → silver → gold

## Agent Rule

Executar **uma task por vez**.

Testes com `tmp_path` como `data_root`. Não alterar fórmulas financeiras nem comportamento de providers.

**Escopo da feature:** invalidação/reprocessamento para **todos** os datasets em `app.core.datasets.DATASETS` e builders gold correspondentes — não apenas `ajustes_bmf`.

**Invariante IPCA:** não modificar `build_for_date` / `_build_ipca_dict`; após invalidar mês(es), rematerializar série diária `IPCA_DICT` até a data final do sync (ver spec FR-009).

**Context:** `bbdb.update(force=True)` → invalidação → `run_daily_sync()` → `read_data()`.

---

## Task 1 — Módulo de invalidação (core)

### Goal

Criar módulo de invalidação com API interna clara, por exemplo `src/app/services/pipeline_invalidation.py`:

- `InvalidationScope` (dataclass): datasets, datas diárias, meses mensais, builders afetados, **dias calendário `ipca_dict` a rematerializar**
- `resolve_invalidation_scope(*, datasets, start_date, end_date, refresh_dates) -> InvalidationScope`
  - `datasets=None` → todos os nomes em `DATASETS`
- `invalidate_bronze_partitions(scope) -> int` (arquivos removidos)
- `invalidate_silver_partitions(scope) -> int`
- `invalidate_gold_persisted(scope, db_path) -> int` (linhas deletadas)

### Files

- `src/app/services/pipeline_invalidation.py` (novo)
- `tests/services/test_pipeline_invalidation.py` (novo)

### Acceptance

- Remove apenas paths sob `bronze_root` / `silver_root` resolvidos
- Cobre granularidade **dia**, **mês** (`ipca_indice`, `projecoes`) e **snapshot** (`feriados`)
- Retorna contadores para logging
- Testes unitários com diretórios temporários

### Do not

- Alterar `update_database()` nesta task
- Alterar `read_data()`
- Alterar `app.lake.gold.builders.ipca_dict`

---

## Task 2 — Integrar invalidação em `update_database()`

### Goal

Quando `force=True`, chamar invalidação **antes** de `run_daily_sync()`, com `settings.activate_path_overlay(env)` ativo.

### Files

- `src/app/services/update_database_service.py`
- `src/app/public/update.py` — adicionar `refresh_dates: list[str] | None = None`
- `src/brazilian_bonds_db/update.py` (se existir reexport fino)

### Acceptance

- `force=False` → zero chamadas de invalidação (regressão)
- `force=True` → invalidação + sync na mesma chamada
- `UpdateDatabaseResult` pode incluir contadores de invalidação (opcional, não breaking)

### Do not

- Mudar semântica de `read_data()`

---

## Task 3 — Escopo `datasets` e mapeamento universal dataset → builder → tabela

### Goal

Filtrar invalidação pelo parâmetro `datasets` de `update()`, com cobertura de **todos** os datasets do pipeline:

| Dataset | Builder / tabela |
|---------|------------------|
| `cdi` | `cdi` / `CDI` |
| `ptax` | `ptax` / `PTAX` |
| `mercado_secundario` | `mercado_secundario` / `MERCADO_SECUNDARIO` |
| `liquidacoes_mercado` | `liquidacoes_mercado` / `LIQUIDACOES_MERCADO` |
| `leiloes` | `leiloes` / `LEILOES` |
| `ajustes_bmf` | `bmf` / `AJUSTES_BMF` |
| `ipca_indice`, `projecoes` | `ipca_dict` / `IPCA_DICT` (ver Task 4) |
| `feriados` | `feriados` / `FERIADOS` |

- `datasets=["ajustes_bmf"]` → só BMF no escopo
- `datasets=None` → **todos** os datasets acima na janela de datas

Reutilizar `BUILDER_TABLE` e `BUILDER_SILVER_DATASETS` de `app.lake.gold`.

### Files

- `src/app/services/pipeline_invalidation.py`
- `tests/services/test_pipeline_invalidation.py`

### Acceptance

- `force=True` + `datasets=["cdi"]` não remove `ajustes_bmf/data=*`
- `force=True` + `datasets=None` inclui todos os datasets registrados em `DATASETS`

---

## Task 4 — `ipca_dict`: invalidação mensal + rebuild da série diária (sem mudar lógica)

### Goal

Implementar escopo e invalidação gold para `ipca_indice` / `projecoes` / `ipca_dict` conforme **spec FR-009**:

1. Derivar `reference_month=YYYY-MM-01` a invalidar (helpers de `gold/incremental`, janela de sync, meses impactados por `refresh_dates`).
2. Remover bronze/silver desses meses.
3. Calcular **`ipca_dict_calendar_days_to_rebuild`**: dias calendário desde o primeiro dia impactado **até** `sync_end_date` / `end_date` do escopo (mesma cobertura que o gold orchestrator usaria para materializar `ipca_dict` na janela).
4. `DELETE FROM IPCA_DICT WHERE data_referencia IN (...)` para esse conjunto de dias (não só um dia isolado).
5. Após sync: gold task `ipca_dict` recebe `ctx.dates` = esse conjunto de dias; materialização via **`build_for_date` existente** (sem alterar builder).

### Files

- `src/app/services/pipeline_invalidation.py`
- `tests/services/test_pipeline_invalidation.py`
- `tests/services/test_update_force_refresh_ipca.py` (novo, ou seção dedicada)

### Acceptance

- Invalidar `reference_month` de maio impacta rematerialização de `IPCA_DICT` para todos os dias calendário necessários até `end_date` do sync, não apenas um dia
- Nenhuma mudança em `src/app/lake/gold/builders/ipca_dict.py` exceto se for estritamente necessário para wiring (preferir zero mudanças)

### Do not

- Duplicar ou reescrever regras de negócio IPCA no módulo de invalidação
- Alterar fórmulas em `build_for_date`

---

## Task 5 — Snapshot `feriados`

### Goal

Se `feriados` ∈ escopo:

- Remover bronze/silver `feriados/snapshot=1`
- Limpar tabela `FERIADOS` no SQLite

### Files

- `src/app/services/pipeline_invalidation.py`
- `tests/services/test_pipeline_invalidation.py`

---

## Task 6 — Testes integração (múltiplos datasets)

### Goal

E2E leve com `tmp_path` — **não** limitar cobertura a BMF:

### 6a — `ajustes_bmf` (caso motivador DAP)

1. Seed bronze/silver/gold para `2026-05-25` só com tickers `DI1*`
2. Mock provider retornando DAP + DI1
3. `update(force=True, datasets=["ajustes_bmf"], ...)`
4. `read_data().ajustes_bmf.fetch_on("2026-05-25")` contém `DAP`

### 6b — dataset diário genérico (ex.: `cdi`)

1. Seed partição com valor incorreto
2. `update(force=True, datasets=["cdi"], ...)`
3. Gold reflete valor do mock após refresh

### 6c — `ipca_dict` (FR-009)

1. Seed silver mensal + gold `IPCA_DICT` para vários dias calendário
2. `update(force=True, datasets=["ipca_indice"], ...)` (ou `projecoes`) invalidando um mês
3. Assert série diária em `IPCA_DICT` recalculada até `end_date` (contagem de datas / campos chave), sem alterar contrato do builder

### Files

- `tests/services/test_update_force_refresh.py` (novo)

---

## Task 7 — Documentação consumidor

### Goal

Documentar nova semântica de `force=True` e parâmetro `refresh_dates`.

### Files

- `README.md`
- `docs/README_PACKAGE_USER_DRAFT.md`
- Docstrings em `src/app/public/update.py` e `src/app/services/update_database_service.py`

### Texto mínimo

- `force=False`: incremental (lacunas)
- `force=True`: apaga bronze/silver/gold no escopo e reprocessa — **todos os datasets** do pipeline quando `datasets=None`
- `ipca_dict`: invalidar mês → rebuild da série diária até data atual do sync (lógica existente)
- Exemplo `ajustes_bmf` + data única (motivador)
- Exemplo `datasets=None` + janela de datas

---

## Task 8 — CLI (opcional)

### Goal

Se `src/app/cli/sync.py` ou entrypoints CLI expõem sync manual, alinhar flag `--force` à mesma semântica de invalidação (sem breaking change para quem já usa CLI).

### Files

- `src/app/cli/sync.py` (se aplicável)
- `run_sync.py` (se aplicável)

### Do not

- Obrigatório para fechar a feature; pode ficar pendente se CLI não for usado por consumidores

---

## Task order (suggested)

```text
1 → 3 → 4 → 5 → 2 → 6 (6a → 6b → 6c) → 7 → (8 opcional)
```

Task 2 depende de 1; tasks 3–5 estendem 1 (Task 4 é crítica para invariante IPCA); task 6 valida fluxo completo após 2.
