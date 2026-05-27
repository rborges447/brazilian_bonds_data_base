# Tasks — 006 Pipeline `vna` (VNA ANBIMA) bronze → silver → gold

## Agent Rule

Execute **one task at a time**.

Antes de implementar, leia a spec:

```text
specs/specs/006-vna-lft-pipeline/spec.md
```

Não misture refatorações gerais com esta feature. O objetivo é adicionar `vna` mantendo os padrões existentes.

### Mapa de dependências

```text
Task 1 (contratos)
  → Tasks 2–4 (provider, bronze, silver)
  → Task 5 (materializer + MATERIALIZERS)
  → Task 7 (migration 012_vna.sql + schema + repository + BUILDER_TABLE)  ← bloqueia 8 e 9
  → Tasks 6, 8 (orchestrator helper, persistence — após Task 7)
  → Task 9 (queries + GoldReader — após Task 7)
  → Task 10 (remover scaffolding + invalidação)  ← bloqueia FR-009/FR-011
  → Task 11 (E2E)
  → Tasks 12–13 (docs + verificação final)
```

**Importante:** o repositório já contém skips temporários (parte deles aparece como placeholder `vna_lft`). A Task 10 existe para removê-los explicitamente e habilitar `vna` — não assumir que “registries centrais” bastam.

---

## Task 1 — Registrar dataset `vna` nos contratos centrais

### Goal

Fazer o sistema reconhecer `vna` como dataset diário canônico.

### Files

- `src/app/core/partitioning.py`
- `src/app/core/datasets.py`
- `src/app/lake/gold/contracts.py`

### Changes

- Adicionar `vna` em `PARTITION_SPECS`:
  - `partition_key="data"`
  - `granularity="day"`
  - `artifact_ext="json"`
  - `date_col_candidates` com aliases de data conhecidos.
- Adicionar `vna` em `DATASETS` com `date_mode="missing_dates"`.
- Confirmar que `assert set(DATASETS) == set(PARTITION_SPECS)` passa com **10** datasets.
- Em gold contracts:
  - adicionar `vna` em `BuilderName` / `BUILDER_NAMES` (novo builder);
  - definir `BUILDER_SILVER_DATASETS["vna"] = ("vna",)`;
  - adicionar `vna` em `PASS_THROUGH_NAMES`;
  - opcional: criar alias de tipo `VnaGoldValue = pd.DataFrame`.

**Ainda não fazer nesta task:** remover skips em `gold/tasks.py`, `gold/incremental.py` ou `pipeline_invalidation.py` (Task 10).

### Tests

- Atualizar/criar testes de contrato para garantir que `DATASETS`, `PARTITION_SPECS` e registries continuam consistentes.

### Do not

- Ainda não implementar extractor, transform ou SQL nesta tarefa.

---

## Task 2 — Provider ANBIMA: método `fetch_vna`

### Goal

Expor método específico no client para buscar VNA por data.

### Files

- `src/app/providers/anbima/client.py`
- `tests/providers/test_anbima_vna.py` ou ampliar `tests/providers/test_anbima_auth.py`/arquivo equivalente

### Changes

Adicionar:

```python
def fetch_vna(self, date_iso: str) -> Optional[Any]:
    return self.fetch_by_date(self.vna_url, date_iso)
```

### Tests

- Mockar `requests.get` ou `fetch_by_date`.
- Verificar que chama `vna_url` com `data=YYYY-MM-DD`.
- Verificar `404` → `None` se o teste estiver no mesmo padrão dos demais.

### Do not

- Não duplicar retry/autenticação.
- Não chamar a API real em teste unitário.

---

## Task 3 — Bronze extractor `vna`

### Goal

Criar extração bronze diária com payload bruto da ANBIMA.

### Files

- `src/app/lake/bronze/extractors/vna.py`
- `src/app/lake/bronze/registry.py`
- `tests/providers` ou `tests/lake` / `tests/contracts` conforme padrão atual

### Changes

Implementar extractor no padrão:

```python
def extract_vna(dates: list[str]) -> ExtractResult:
    spec = get_partition_spec("vna")
    client = AnbimaClient()
    return extract_json_partitions(
        spec,
        dates,
        lambda day: client.fetch_vna(day),
    )
```

Registrar em `EXTRACTORS`.

### Tests

- Mockar `AnbimaClient.fetch_vna`.
- Rodar extractor para uma data.
- Verificar criação de `bronze/vna/data=YYYY-MM-DD/part.json`.
- Verificar `ExtractResult.segment_keys` / `row_count` conforme padrão do helper usado.

### Do not

- Não normalizar campos no bronze.

---

## Task 4 — Silver transform `vna`

### Goal

Normalizar o payload bruto (lista com `data_referencia` + `titulos[]`) em DataFrame tabular.

### Files

- `src/app/lake/silver/transforms/vna.py`
- `src/app/lake/silver/registry.py`
- `src/app/lake/silver/schemas.py` se o projeto centraliza rename/numeric maps ali
- `tests/lake` ou `tests/contracts/test_silver.py`

### Changes

Implementar `normalize_partition(df_raw, partition_value, dates=None)` retornando sempre (1 linha por título):

```text
data_referencia
codigo_selic
tipo_correcao
index
data_validade
vna
```

Regras:

- aceitar lista, dict ou DataFrame já expandido;
- mapear aliases de data para `data_referencia`;
- explodir/normalizar `titulos`;
- converter `data_referencia` e `data_validade` para ISO;
- converter `codigo_selic` para `int`;
- converter `index` e `vna` para `float`;
- filtrar por `dates` ou `partition_value`;
- dropar linhas inválidas;
- deduplicar por (`data_referencia`, `codigo_selic`), mantendo o último registro.

Registrar em `TRANSFORMS`.

### Tests

Casos mínimos:

1. Payload no formato real (`data_referencia` + `titulos[]`) gera N linhas.
2. `codigo_selic` vindo como string numérica vira `int`.
3. `index` e `vna` aceitam vírgula decimal.
4. Filtro por `partition_value` remove datas diferentes.
5. Payload vazio retorna DataFrame vazio com colunas corretas.

### Do not

- Não persistir em SQLite nesta tarefa.

---

## Task 5 — Gold materializer e registry (`vna`)

### Goal

Materializar `vna` a partir do silver como DataFrame gold-ready.

### Files

- `src/app/lake/gold/materializers/vna.py`
- `src/app/lake/gold/registry.py`
- `src/app/lake/gold/builders/vna_lft.py` — placeholder legado (avaliar remoção/ajuste após `vna` existir)
- `tests/contracts/test_provider_contracts.py` ou teste gold específico

### Changes

Criar `from_silver(silver, ctx)`:

- exigir `silver["vna"]`;
- retornar DataFrame com `data_referencia`, `codigo_selic`, `tipo_correcao`, `index`, `data_validade`, `vna` e `vna_ajustado`;
- garantir tipos (conforme contrato silver);
- adicionar `vna_ajustado` como coluna presente (inicialmente `None`/SQL NULL);
- filtrar por `ctx.dates` se necessário (usar `resolve_enforce_dates` / `prepare_tabular_output` de `_tabular.py`, como `cdi.py`);
- remover duplicatas por (`data_referencia`, `codigo_selic`).

Registrar em `MATERIALIZERS` (`src/app/lake/gold/registry.py`):

```python
"vna": vna_from_silver,
```

Hoje `registry.build("vna", ...)` não existe; após esta task, `vna` deve ser pass-through materializado via `MATERIALIZERS`.

### Tests

- `materialize("vna", ctx=BuilderContext(dates=[...]))` (ou helper explícito se você adicionar na Task 6).
- Confirmar colunas e valores.

### Do not

- Não criar fórmula financeira. É pass-through.

---

## Task 6 — Orchestrator helper para `vna`

### Goal

Adicionar método explícito no `GoldOrchestrator`, seguindo o padrão dos demais datasets diários.

### Files

- `src/app/lake/gold/orchestrator.py`
- `src/app/cli/gold.py` se `_materialize_builder` tiver dispatch explícito

### Changes

Adicionar:

```python
def materialize_vna(self, dates: list[str], ctx: BuilderContext | None = None) -> GoldMaterialized:
    ...
    return self.materialize("vna", ctx=run_ctx)
```

Atualizar qualquer dispatch manual que mapeia `task.name` para método (`_materialize_builder`).

### Tests

- Testar dispatch gold para `vna`.

### Do not

- Não alterar comportamento de IPCA ou BMF.

---

## Task 7 — Migration `012_vna.sql`, schema, repository e `BUILDER_TABLE`

### Goal

Criar a tabela gold **`VNA`** no SQLite via migration versionada e preparar persistência/consulta. Esta task implementa **FR-006** da spec.

Sem a migration, `update()` pode rodar sync, mas **persistência e `read_data().vna` falham** (tabela inexistente).

### Files

- `src/app/database/migrations/012_vna.sql` **(novo — entregável principal desta task)**
- `src/app/database/schema.py`
- `src/app/repositories/vna.py`
- `src/app/lake/gold/incremental.py` — entrada em `BUILDER_TABLE`
- `tests/database/test_migrations_v2.py`
- `tests/database/test_repositories_v2.py`

### Migration `012_vna.sql`

Criar arquivo após `011_indexes.sql`. O runner (`src/app/database/migrate.py`) aplica automaticamente por ordem lexicográfica e registra versão `012` em `schema_migrations`.

Conteúdo esperado (copiar/adaptar da spec FR-006):

```sql
-- VNA diário (ANBIMA): 1 linha por data_referencia + codigo_selic.

CREATE TABLE IF NOT EXISTS VNA (
    data_referencia TEXT NOT NULL,
    codigo_selic INTEGER NOT NULL,
    tipo_correcao TEXT NOT NULL,
    "index" REAL NOT NULL,
    data_validade TEXT NOT NULL,
    vna REAL NOT NULL,
    vna_ajustado REAL,
    PRIMARY KEY (data_referencia, codigo_selic)
);

CREATE INDEX IF NOT EXISTS idx_vna_data ON VNA (data_referencia);
```

Checklist da migration:

- [ ] Arquivo nomeado `012_vna.sql` (prefixo `012` = versão em `schema_migrations`).
- [ ] `CREATE TABLE IF NOT EXISTS` (idempotente em re-run parcial).
- [ ] PK composta `(data_referencia, codigo_selic)`.
- [ ] Coluna reservada SQL: `"index"` no DDL; nome lógico `index` no Python/DataFrame.
- [ ] `vna_ajustado` sem `NOT NULL` (nullable).
- [ ] Índice `idx_vna_data` em `data_referencia` para queries por data.

**Não** alterar `migrate.py` — descoberta de `*.sql` já existe.

### Schema changes (`schema.py`)

- `TABLE_VNA = "VNA"`
- `VNA_COLUMNS = ("data_referencia", "codigo_selic", "tipo_correcao", "index", "data_validade", "vna", "vna_ajustado")`
- incluir `TABLE_VNA` em `BUSINESS_TABLES_V2` (obrigatório para `test_migrations_v2`)
- exportar em `__all__`

### Repository

Criar `VnaRepository`:

```python
class VnaRepository:
    table_name: str = TABLE_VNA

    def upsert(self, df: pd.DataFrame, *, db_path: Any = None) -> int:
        return upsert_dataframe(self.table_name, df, VNA_COLUMNS, db_path=db_path)
```

Upsert usa `INSERT OR REPLACE` — compatível com PK composta (mesmo padrão de tabelas multi-linha).

### Incremental (`BUILDER_TABLE`)

Em `src/app/lake/gold/incremental.py`:

```python
"vna": (TABLE_VNA, "data_referencia"),
```

Coluna de data para gaps/invalidação diária: `data_referencia` (DELETE por data remove todos os títulos daquele dia).

**Ainda não remover** skips do placeholder em `candidates_for_builder` — Task 10.

### Tests

**Migration (`test_migrations_v2.py`):**

- `apply_migrations(tmp_db)` → tabela `VNA` existe.
- `TABLE_VNA in BUSINESS_TABLES_V2` (teste existente que itera `BUSINESS_TABLES_V2` deve passar sem alterar lista manualmente além de schema).
- Opcional: assert em colunas via `PRAGMA table_info(VNA)` — 7 colunas, PK em `(data_referencia, codigo_selic)`.

**Repository (`test_repositories_v2.py`):**

- Upsert de 2 linhas (mesma `data_referencia`, `codigo_selic` diferentes) → 2 rows.
- Re-upsert da mesma chave atualiza `vna`.
- Linha com `vna_ajustado=None` persiste (NULL).
- DataFrame com coluna extra ou faltando → `validate_dataframe_columns` falha.

### Prerequisite for downstream tasks

- **Task 8** (gold persistence) e **Task 9** (queries / `GoldReader`) só depois desta task.
- **Task 11** (E2E): `update()` aplica migration automaticamente; validar que `tmp_path` DB recebe `VNA` no primeiro `update`.

### Do not

- Não colocar DDL apenas em comentários — o arquivo `012_vna.sql` deve existir no repositório.
- Não reutilizar nome de tabela `VNA_LFT` (legado do placeholder).

---

## Task 8 — Persistência gold

### Goal

Persistir o resultado gold `vna` no SQLite.

### Prerequisite

**Task 7** — tabela `VNA` deve existir (`012_vna.sql` aplicada).

### Files

- `src/app/services/gold_persistence.py`
- `tests/services` ou `tests/database` conforme padrão

### Changes

- Importar `VnaRepository`.
- Remover o branch especial que faz `raise NotImplementedError` para o placeholder `vna_lft`.
- Tratar `vna` como os demais builders tabulares — adicionar ao dict `repos`:

```python
"vna": VnaRepository(),
```

(ou equivalente consistente com o padrão do arquivo após a remoção do branch).

### Tests

- `persist_materialized(GoldMaterialized(name="vna", ...))` grava linhas.
- DataFrame inválido levanta erro compatível com os demais.

---

## Task 9 — Queries e `GoldReader`

### Goal

Expor leitura pública `read_data().vna`.

### Prerequisite

**Task 7** — queries referenciam `FROM VNA`; migration deve estar aplicada.

### Files

- `src/app/database/queries/vna_all.sql`
- `src/app/database/queries/vna_latest.sql`
- `src/app/database/queries/vna_on_date.sql`
- `src/app/database/queries/vna_range.sql`
- `src/app/database/queries/_README.md`
- `src/app/database/readers/gold_reader.py`
- `docs/gold_reader_public_api.md`
- `tests/database/test_gold_reader.py`
- `tests/public/test_read_data_public_api.py`

### Query patterns

`all`:

```sql
SELECT data_referencia, codigo_selic, tipo_correcao, "index", data_validade, vna, vna_ajustado
FROM VNA
ORDER BY data_referencia, codigo_selic;
```

`on_date`:

```sql
SELECT data_referencia, codigo_selic, tipo_correcao, "index", data_validade, vna, vna_ajustado
FROM VNA
WHERE data_referencia = ?
ORDER BY data_referencia, codigo_selic;
```

`range`:

```sql
SELECT data_referencia, codigo_selic, tipo_correcao, "index", data_validade, vna, vna_ajustado
FROM VNA
WHERE data_referencia BETWEEN ? AND ?
ORDER BY data_referencia, codigo_selic;
```

`latest` com CTE:

```sql
WITH latest_dates AS (
    SELECT data_referencia
    FROM VNA
    GROUP BY data_referencia
    ORDER BY data_referencia DESC
    LIMIT ?
)
SELECT data_referencia, codigo_selic, tipo_correcao, "index", data_validade, vna, vna_ajustado
FROM VNA
WHERE data_referencia IN (SELECT data_referencia FROM latest_dates)
ORDER BY data_referencia DESC, codigo_selic;
```

### GoldReader

Adicionar:

```python
self.vna = DateSeriesTableReader(query_prefix="vna", db_path=db_path)
```

### Tests

- `fetch_all`
- `fetch_on`
- `fetch_range`
- `fetch_latest`
- `hasattr(read_data(), "vna")`

---

## Task 10 — Remover scaffolding e integrar force refresh / sync gold (`vna`)

### Goal

Habilitar `vna` no sync gold incremental e na invalidação destrutiva (`update(force=True)`). Esta task implementa **FR-009** e **FR-011** da spec.

### Files

- `src/app/lake/gold/tasks.py`
- `src/app/lake/gold/incremental.py`
- `src/app/services/pipeline_invalidation.py`
- `tests/services/test_pipeline_invalidation.py`
- `tests/services/test_update_force_refresh.py`
- `tests/lake/gold/test_orchestrator_scaffold.py` (se necessário)

### Changes — `gold/tasks.py`

Garantir que `resolve_gold_tasks` inclua o builder `vna` (e remover exclusões temporárias ligadas ao placeholder `vna_lft` quando aplicável).

```python
# Antes (scaffolding):
names = tuple(n for n in BUILDER_NAMES if n != "vna_lft")

# Depois:
names = BUILDER_NAMES  # ou equivalente sem filtro
```

Com Task 1 + Task 7 concluídas, `resolve_gold_tasks` deve passar a emitir `GoldTask(name="vna", dates=[...])` quando houver gaps.

### Changes — `gold/incremental.py`

Remover o(s) early-return(s)/skips que desabilitam candidatos (hoje associados ao placeholder `vna_lft`) e garantir que `vna` siga o fluxo diário padrão (`sync_business_days` + silver ready + `BUILDER_TABLE`).

```python
# Remover esta condição (ou equivalente):
if builder == "feriados" or builder == "vna_lft":
    return []
```

Manter apenas o caso especial de `feriados`. `vna` deve seguir o fluxo diário padrão (`sync_business_days` + silver ready + `BUILDER_TABLE` da Task 7).

### Changes — `pipeline_invalidation.py`

Remover skips hard-coded:

1. Em `_dataset_to_builder`: remover `if builder == "vna_lft": continue`.
2. Em `_builders_for_datasets`: remover `builder != "vna_lft"`.

Com `BUILDER_SILVER_DATASETS["vna"] = ("vna",)`, o mapeamento automático passa a incluir:

```text
vna (dataset) → vna (builder) → VNA (table) → data_referencia (col)
```

### Changes — testes existentes a atualizar

`tests/services/test_pipeline_invalidation.py`:

- `test_resolve_all_datasets_when_none`: `len(scope.datasets) == 10` (não 9); remover `assert "vna_lft" not in scope.builders` ou ajustar para refletir escopo completo quando `vna_lft` estiver em `DATASETS`;
- adicionar `("vna", "vna")` ao `@pytest.mark.parametrize` de `test_resolve_maps_dataset_to_builder`;
- novos testes de invalidação bronze/silver/gold para `vna` em uma data (espelhar `test_invalidate_gold_daily` de `cdi`).

### Tests (novos cenários)

- Seed bronze/silver/gold de `vna` em `tmp_path`.
- `resolve_invalidation_scope(datasets=["vna"], refresh_dates=[...])` inclui builder `vna` e partições corretas.
- Rodar invalidação para uma data: arquivos removidos + `DELETE FROM VNA WHERE data_referencia = ?` (todas as linhas da data).
- `update(..., force=True, datasets=["vna"], ...)` com mock reprocessa sem tocar `cdi` / outros datasets.
- `resolve_gold_tasks` inclui `vna` quando há gap gold/silver.

### Do not

- Não apagar outros datasets quando `datasets=["vna"]`.
- Não reintroduzir exceções “temporárias” (placeholders) após esta task.

### Prerequisite

Tasks 1, 5, 7 e 8 concluídas (contratos, materializer, `BUILDER_TABLE`, persistence).

---

## Task 11 — E2E leve de `update` + `read_data` (`vna`)

### Goal

Validar o fluxo completo de consumidor.

### Files

- `tests/integration/test_vna_pipeline.py` ou ampliar `tests/integration/test_sync_full_range.py`
- `tests/public/test_update_public_api.py`

### Scenario

1. Usar `tmp_path` como `data_root`.
2. Mockar `AnbimaClient.fetch_vna` para retornar payload de uma data.
3. Chamar:

```python
bbdb.update(
    data_root=tmp_path,
    datasets=["vna"],
    start_date="2026-05-20",
    end_date="2026-05-20",
)
```

4. Ler:

```python
bbdb.read_data(data_root=tmp_path).vna.fetch_on("2026-05-20")
```

5. Assert:

```text
data_referencia == "2026-05-20"
codigo_selic == 210100 (exemplo LFT do mock)
vna == valor mockado
```

### Prerequisite

Task 10 concluída (sync gold e invalidação habilitados).

### Do not

- Não depender da API real da ANBIMA.

---

## Task 12 — Documentação

### Goal

Documentar `vna` para o usuário final do pacote.

### Files

- `README.md`
- `docs/README_PACKAGE_USER_DRAFT.md`
- `docs/gold_reader_public_api.md`
- docstring de `src/app/database/readers/gold_reader.py`

### Conteúdo mínimo

Exemplo:

```python
import brazilian_bonds_db as bbdb

bbdb.update(
    data_root="./data/brazilian_bonds_db",
    datasets=["vna"],
    start_date="2026-05-20",
    end_date="2026-05-20",
)

vna = bbdb.read_data(data_root="./data/brazilian_bonds_db").vna
print(vna.fetch_latest(5))
```

Explicar:

- fonte: ANBIMA;
- granularidade: diária;
- colunas: `data_referencia`, `codigo_selic`, `tipo_correcao`, `index`, `data_validade`, `vna`, `vna_ajustado`;
- `force=True` reprocessa o escopo.

---

## Task 13 — Verificação final

### Goal

Rodar suíte focada e corrigir regressões.

### Commands

```bash
pytest tests/providers tests/contracts tests/database tests/public tests/services -q
pytest tests/integration -q
```

Se a suíte completa for viável:

```bash
pytest -q
```

### Acceptance

- `012_vna.sql` presente; `apply_migrations()` cria `VNA` + `idx_vna_data`.
- Nenhum `NotImplementedError` para `vna` em `registry.build`, `gold_persistence` ou fluxo sync.
- Nenhum skip hard-coded que impeça `vna` em `gold/tasks.py`, `gold/incremental.py`, `pipeline_invalidation.py`.
- `read_data().vna` disponível.
- `update(datasets=["vna"])` funciona com mock (migration → bronze → silver → gold → SQLite).
- `update(..., force=True, datasets=["vna"], ...)` invalida e reprocessa escopo sem side effects.
- `len(DATASETS) == 10`; testes de invalidação alinhados com a spec.
