# Feature Spec — Pipeline `vna` (VNA ANBIMA) bronze → silver → gold

## Feature Name

`006-vna-lft-pipeline` (implementa o dataset `vna`)

## Status and dependencies

- **Prerequisites:** `001-public-database-api`, `003-public-gold-reader-api`, `005-force-refresh-pipeline`
- **Contexto atual (código):** o repositório tem referências parciais a um placeholder `vna_lft`, mas **o dataset correto** a ser implementado é `vna` (tabular, 1 linha por título). Implementação desta spec deve **adicionar** as camadas faltantes para `vna` e **remover/ajustar** os skips listados em [Scaffolding temporário](#scaffolding-temporário-a-remover).
- **Scope:** implementar o dataset diário `vna` em todas as camadas do pipeline: provider, bronze, silver, gold, SQLite, repository, queries, `GoldReader`, `update()` e `read_data()`; habilitar sync incremental, materialização gold e `update(force=True)` no mesmo padrão de `cdi` / `ptax`.
- **Out of scope:** cálculos derivados de LFT, interpolação, uso de VNA em precificação de títulos, APIs externas além da ANBIMA, PostgreSQL.

### Scaffolding temporário (a remover)

Enquanto `vna` não estiver implementado, o código atual ainda contém scaffolding/locks (parte deles aparece como `vna_lft`). Esta feature só está completa quando **não restar** nenhum item abaixo:

| Arquivo | Comportamento atual | Ação na implementação |
|---------|---------------------|------------------------|
| `src/app/core/partitioning.py` | `vna` ausente de `PARTITION_SPECS` | Adicionar spec diária (FR-001) |
| `src/app/core/datasets.py` | `vna` ausente de `DATASETS` | Adicionar com `date_mode="missing_dates"` |
| `src/app/lake/bronze/registry.py` | sem extractor `vna` | Registrar extractor (FR-003) |
| `src/app/lake/silver/registry.py` | sem transform `vna` | Registrar transform (FR-004) |
| `src/app/lake/gold/contracts.py` | sem `BUILDER_SILVER_DATASETS["vna"]`; `PASS_THROUGH_NAMES` sem `vna` | Apontar para silver `("vna",)`; incluir em pass-through |
| `src/app/lake/gold/registry.py` | `vna` ausente de `MATERIALIZERS` | Registrar materializer (FR-005) |
| `src/app/lake/gold/tasks.py` | há exclusões temporárias ligadas ao placeholder `vna_lft` | Ajustar para incluir o builder `vna` (FR-011) |
| `src/app/lake/gold/incremental.py` | lógica atual tem skip para `vna_lft`; `BUILDER_TABLE` sem `vna` | Habilitar candidatos diários e mapear `vna` → `VNA` / `data_referencia` (FR-011) |
| `src/app/services/pipeline_invalidation.py` | lógica atual tem skip para `vna_lft` | Invalidação deve cobrir `vna` (FR-009/FR-011) |
| `src/app/services/gold_persistence.py` | branch especial `NotImplementedError` para `vna_lft` | Persistir `vna` via repository (FR-007) |
| `src/app/database/migrations/` | Sem `012_vna.sql` | Criar migration versionada da tabela `VNA` (FR-006) |
| `src/app/database/schema.py` | Sem `TABLE_VNA` / `VNA_COLUMNS` | Adicionar símbolos e `BUSINESS_TABLES_V2` (FR-006) |
| `src/app/database/readers/gold_reader.py` | Sem atributo `vna` | Expor `DateSeriesTableReader` (FR-008) |
| `tests/services/test_pipeline_invalidation.py` | assume dataset/builders atuais; contagens e parametrizações não incluem `vna` | Atualizar expectativas para 10 datasets e mapeamento `vna` |

**Nota sobre a spec `005`:** ela documenta a exceção temporária *“exceto `vna_lft` se ainda não implementado”*. Ao concluir esta feature, a exceção deixa de existir, mas o dataset implementado é `vna` (não `vna_lft`).

## Objective

Adicionar ao sistema o dado diário **VNA (ANBIMA)**, vindo da ANBIMA, com fluxo completo:

```text
AnbimaClient → bronze/vna → silver/vna → gold VNA (SQLite) → read_data().vna
                              ↑
                    apply_migrations() cria/atualiza tabela VNA
```

`update()` já executa migrations antes do sync (`update_database` → `run_migrations`). A tabela `VNA` deve existir **antes** de persistir gold ou de `read_data().vna` consultar queries.

A tabela gold final deve ser simples e estável (1 linha por `data_referencia` + `codigo_selic`, refletindo os títulos dentro do payload):

| coluna | tipo lógico | descrição |
|--------|-------------|-----------|
| `data_referencia` | ISO `YYYY-MM-DD` | data de referência do VNA (partição diária) |
| `codigo_selic` | `int` | identificador do título (ex.: `210100` para LFT) |
| `tipo_correcao` | `str` | tipo de correção (ex.: `P`, `O`) |
| `index` | `float` | índice publicado pela ANBIMA para o título na data |
| `data_validade` | ISO `YYYY-MM-DD` | data de validade da cotação do título |
| `vna` | `float` | VNA publicado pela ANBIMA |
| `vna_ajustado` | `float \| null` | reservado para ajuste futuro; inicialmente vazio (NULL) |

O dado tem **granularidade diária** (partição por `data_referencia`). `update()` e `read_data()` devem seguir os mesmos padrões dos outros datasets diários (`cdi`, `ptax`, etc.).

## Functional requirements

### FR-001 — Dataset canônico `vna`

Registrar `vna` como dataset diário em:

- `app.core.partitioning.PARTITION_SPECS`
- `app.core.datasets.DATASETS` (assert com `PARTITION_SPECS` passa a valer 10 datasets)
- bronze registry (`EXTRACTORS`)
- silver registry (`TRANSFORMS`)
- gold contracts (`BUILDER_SILVER_DATASETS`, `PASS_THROUGH_NAMES`)
- gold registry (`MATERIALIZERS`)
- gold incremental (`BUILDER_TABLE` — ver FR-011)
- migration SQLite `012_vna.sql` + `schema.py` / `BUSINESS_TABLES_V2` (FR-006)
- force refresh / invalidação (ver FR-011)

Configuração esperada:

| Campo | Valor |
|-------|-------|
| dataset | `vna` |
| granularidade | `day` |
| partition key | `data` |
| bronze artifact | `json` |
| silver artifact | `parquet` |
| gold builder | `vna` |
| tabela SQL | `VNA` |
| migration | `012_vna.sql` (versão `012` em `schema_migrations`) |
| sync window | dias úteis (`sync_business_days`), como `cdi` / `mercado_secundario` |
| date_mode | `missing_dates` |

### FR-002 — Provider ANBIMA

Adicionar método explícito no `AnbimaClient`:

```python
def fetch_vna(self, date_iso: str) -> Optional[Any]:
    return self.fetch_by_date(self.vna_url, date_iso)
```

A implementação deve reutilizar autenticação, retry, timeout e tratamento de `404` já existentes em `fetch_by_date`.

Não duplicar lógica HTTP fora do client.

### FR-003 — Bronze `vna`

Criar extractor bronze diário:

```text
src/app/lake/bronze/extractors/vna.py
```

Comportamento:

- recebe lista de datas ISO;
- para cada data, chama `AnbimaClient.fetch_vna(date_iso)`;
- grava payload bruto em `bronze/vna/data=YYYY-MM-DD/part.json`;
- segue o padrão de `mercado_secundario` / `extract_json_partitions`;
- se a ANBIMA retornar `None` / `404`, não deve quebrar o pipeline; deve deixar a partição ausente, como nos demais extractors.

### FR-004 — Silver `vna`

Criar transform silver:

```text
src/app/lake/silver/transforms/vna.py
```

Formato de entrada esperado do provider (por data):

```text
[
  {
    "data_referencia": "YYYY-MM-DD",
    "titulos": [
      {
        "codigo_selic": "...",
        "tipo_correcao": "...",
        "index": ...,
        "data_validade": "YYYY-MM-DD",
        "vna": ...
      },
      ...
    ]
  }
]
```

Contrato de saída obrigatório (silver tabular, 1 linha por título):

```text
data_referencia: string ISO YYYY-MM-DD
codigo_selic: int
tipo_correcao: str
index: float
data_validade: string ISO YYYY-MM-DD
vna: float
```

A normalização deve:

- aceitar payload em lista ou objeto único;
- explodir/normalizar `titulos` para 1 linha por título;
- converter `data_referencia` e `data_validade` para ISO `YYYY-MM-DD`;
- converter `codigo_selic` para `int` (aceitar string numérica no payload);
- converter `index` e `vna` para `float` (aceitar vírgula decimal quando necessário);
- filtrar pela `partition_value` / `dates`, como os demais datasets diários;
- remover linhas sem `data_referencia` ou sem `codigo_selic` ou sem `vna`;
- retornar DataFrame vazio com as colunas canônicas quando não houver dados válidos.

Aliases mínimos aceitos (por robustez) — expandir somente se aparecer no provider real:

- `data_referencia`: `data_referencia`, `data`, `Data`, `dt_referencia`
- `titulos`: `titulos`, `Titulos`, `itens`
- `codigo_selic`: `codigo_selic`, `codigoSelic`, `codigo`, `cod_selic`
- `tipo_correcao`: `tipo_correcao`, `tipoCorrecao`, `correcao`
- `index`: `index`, `indice`, `índice`
- `data_validade`: `data_validade`, `dataValidade`, `validade`
- `vna`: `vna`, `VNA`, `valor_vna`, `valor`

### FR-005 — Gold materialization (`vna`)

Implementar gold como pass-through tabular simples.

Opção preferencial:

```text
src/app/lake/gold/materializers/vna.py
```

Comportamento:

- recebe `silver["vna"]`;
- valida/seleciona `data_referencia`, `codigo_selic`, `tipo_correcao`, `index`, `data_validade`, `vna`;
- garante tipos (`codigo_selic` int; demais conforme contrato silver);
- adiciona `vna_ajustado` como coluna **presente** no gold (inicialmente `None`/SQL NULL);
- remove duplicatas por chave natural (`data_referencia`, `codigo_selic`), mantendo o último registro em ordem estável;
- retorna DataFrame com colunas exatamente na ordem:\n  `(\"data_referencia\", \"codigo_selic\", \"tipo_correcao\", \"index\", \"data_validade\", \"vna\", \"vna_ajustado\")`.

Atualizar:

- `PASS_THROUGH_NAMES` para incluir `vna`;
- `BUILDER_SILVER_DATASETS["vna"] = ("vna",)`;
- `MATERIALIZERS["vna"] = vna_from_silver`.

Materializer deve reutilizar helpers de `src/app/lake/gold/materializers/_tabular.py` quando aplicável (`prepare_tabular_output`, `resolve_enforce_dates`), no mesmo espírito de `cdi.py` / `ptax.py`.

### FR-006 — SQLite / schema / migration (`VNA`)

Adicionar a tabela gold **`VNA`** via **migration versionada** no mesmo mecanismo das demais tabelas de negócio (`001` … `011`).

#### Arquivo de migration (obrigatório)

| Item | Valor |
|------|-------|
| Caminho | `src/app/database/migrations/012_vna.sql` |
| Versão registrada | `012` (prefixo do nome do arquivo, gravado em `schema_migrations`) |
| Ordem | Após `011_indexes.sql` (última migration existente hoje) |
| Descoberta | Automática: `apply_migrations()` lista `*.sql` em ordem lexicográfica (`migrate.py`) |
| Idempotência | `CREATE TABLE IF NOT EXISTS` + `CREATE INDEX IF NOT EXISTS` |

Conteúdo mínimo do arquivo (alinhado ao materializer gold e ao repository):

```sql
-- VNA diário (ANBIMA): 1 linha por data_referencia + codigo_selic.
-- Colunas alinhadas com lake.gold.materializers.vna e app.repositories.vna.

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

Notas de DDL:

- A coluna `index` é palavra reservada em SQL — usar `"index"` no DDL e mapear para o nome lógico `index` em `VNA_COLUMNS` / DataFrame.
- `vna_ajustado` é **nullable** (reservada; gold inicial grava NULL).
- Chave primária composta `(data_referencia, codigo_selic)` — upsert usa `INSERT OR REPLACE` (mesmo padrão de `MERCADO_SECUNDARIO` / `LEILOES`).
- Índice em `data_referencia` acelera `fetch_on`, `fetch_range` e `fetch_latest` (padrão de `011_indexes.sql`).

#### Schema Python (obrigatório)

Atualizar `src/app/database/schema.py`:

- `TABLE_VNA = "VNA"`
- `VNA_COLUMNS = ("data_referencia", "codigo_selic", "tipo_correcao", "index", "data_validade", "vna", "vna_ajustado")`
- incluir `TABLE_VNA` em `BUSINESS_TABLES_V2` (ordem sugerida: após séries diárias simples, antes ou depois de tabelas multi-linha — manter ordem alfabética ou agrupamento existente no arquivo)
- exportar `TABLE_VNA`, `VNA_COLUMNS` em `__all__`

`validate_dataframe_columns` e `VnaRepository` devem usar **exatamente** `VNA_COLUMNS` (mesmo contrato que `CDI_COLUMNS` / `CdiRepository`).

#### Aplicação da migration em runtime

- `apply_migrations(db_path=...)` ( `src/app/database/migrate.py` ) aplica `012_vna.sql` uma vez por banco, registrando versão `012` em `schema_migrations`.
- `update()` / `update_database()` chama `run_migrations()` **antes** do sync — bancos novos e existentes recebem a tabela ao rodar `bbdb.update(...)`.
- Não é necessário alterar `migrate.py` nem criar manifest manual — basta adicionar o arquivo `012_vna.sql`.

#### Testes de migration (obrigatório)

- `tests/database/test_migrations_v2.py`: após `apply_migrations`, `VNA` ∈ tabelas e `TABLE_VNA` ∈ `BUSINESS_TABLES_V2`.
- Teste dedicado (neste arquivo ou `test_repositories_v2.py`): schema da tabela — colunas, PK composta, `vna_ajustado` aceita NULL.
- Opcional: `PRAGMA table_info(VNA)` ou query em `sqlite_master` para validar DDL aplicado.

#### Dependências downstream

Só após FR-006 concluído:

- **FR-007** — `VnaRepository.upsert` grava em `VNA`;
- **FR-008** — queries `vna_*.sql` referenciam `FROM VNA`;
- **FR-009** — `invalidate_gold_persisted` faz `DELETE FROM VNA WHERE data_referencia IN (...)`.

### FR-007 — Repository e persistência

Criar repository:

```text
src/app/repositories/vna.py
```

Comportamento:

- usar `upsert_dataframe`;
- chave natural: (`data_referencia`, `codigo_selic`) via primary key da tabela;
- validar colunas com `VNA_COLUMNS`.

Atualizar `src/app/services/gold_persistence.py`:

- importar `VnaRepository`;
- persistir `name == "vna"` como DataFrame;
- remover o comportamento temporário de `NotImplementedError` que hoje existe para o placeholder `vna_lft`.

### FR-008 — Queries SQL e reader público

Criar queries:

```text
src/app/database/queries/vna_all.sql
src/app/database/queries/vna_latest.sql
src/app/database/queries/vna_on_date.sql
src/app/database/queries/vna_range.sql
```

Semântica igual aos demais datasets diários:

- `fetch_all()` retorna tudo ordenado por `data_referencia` asc (e `codigo_selic` asc como tie-break);
- `fetch_on(date)` retorna todas as linhas daquela data (todos os títulos);
- `fetch_range(start, end)` retorna intervalo inclusivo (todas as linhas cujas datas estejam no range);
- `fetch_latest(n)` retorna as últimas `n` datas distintas (todos os títulos dessas datas), usando o padrão CTE da spec `004`.

Adicionar em `GoldReader`:

```python
self.vna = DateSeriesTableReader(query_prefix="vna", db_path=db_path)
```

Depois disso, o uso público esperado é:

```python
import brazilian_bonds_db as bbdb

bbdb.update(datasets=["vna"], start_date="2026-05-20", end_date="2026-05-20")
df = bbdb.read_data().vna.fetch_on("2026-05-20")
```

### FR-009 — Integração com `update(force=True)`

`vna` deve funcionar com o comportamento da feature `005`:

```python
bbdb.update(
    datasets=["vna"],
    start_date="2026-05-20",
    end_date="2026-05-20",
    force=True,
)
```

Resultado esperado:

- remove bronze `vna/data=2026-05-20/part.json`;
- remove silver `vna/data=2026-05-20/part.parquet`;
- deleta `VNA` no SQLite para `data_referencia = '2026-05-20'` (todas as linhas daquela data);
- reextrai, renormaliza e persiste novamente.

**Implementação obrigatória (não basta “registries centrais”):** o código atual tem skips hard-coded. Além de completar FR-001 e FR-006, é necessário:

1. **`pipeline_invalidation.py`** — remover os skips hard-coded hoje associados ao placeholder `vna_lft` e garantir que o dataset/builder `vna` seja resolvido via registries (`BUILDER_SILVER_DATASETS["vna"] = ("vna",)`).
2. **`gold/incremental.py`** — adicionar `"vna": (TABLE_VNA, "data_referencia")` em `BUILDER_TABLE`; remover early-return vazio que hoje desabilita candidatos para o placeholder.
3. **`gold/tasks.py`** — garantir que `resolve_gold_tasks` inclua o builder `vna`.
4. **`sync_runner.py`** — nenhuma alteração esperada: `_allowed_task_names` já propaga builder quando o silver dataset está no escopo; passa a funcionar após FR-001.

Testes a atualizar/criar:

- `tests/services/test_pipeline_invalidation.py` — contagem de datasets (`10`), presença de `vna` no escopo quando aplicável, mapeamento `("vna", "vna")` no parametrize de builders, invalidação bronze/silver/gold de uma data;
- `tests/services/test_update_force_refresh.py` — cenário `datasets=["vna"]` com mock.

### FR-011 — Habilitar pipeline gold/sync (remover scaffolding)

Complementa FR-001 e FR-009. Objetivo: `vna` participa do sync diário, detecção de gaps e materialização gold da mesma forma que `cdi`.

Checklist de arquivos (todos devem estar livres de skip/placeholder ao final):

| Módulo | Requisito |
|--------|-----------|
| `gold/tasks.py` | `vna` entra em `resolve_gold_tasks` |
| `gold/incremental.py` | candidatos diários + `BUILDER_TABLE` |
| `gold/registry.py` | `MATERIALIZERS["vna"]` |
| `gold/orchestrator.py` | opcional: `materialize_vna` + dispatch em `cli/gold.py` |
| `gold_persistence.py` | upsert via repository, sem branch especial de erro |
| `pipeline_invalidation.py` | invalidação por data no escopo |

Sync incremental esperado:

- bronze: `missing_partition_values` para dias úteis sem partição;
- silver: `missing_silver_partitions` quando bronze existe e silver falta;
- gold: `missing_materialize_dates` quando silver existe e linha SQL falta.

`update(datasets=["vna"], ...)` **não** deve puxar builders de outros datasets (mesmo contrato já validado para `cdi` vs `ajustes_bmf` na spec `005`).

### FR-010 — Documentação

Atualizar:

- `README.md`
- `docs/README_PACKAGE_USER_DRAFT.md`
- `docs/gold_reader_public_api.md`
- docstrings relevantes em `GoldReader`, `public.update` se houver lista de datasets

Conteúdo mínimo:

- `vna` é série diária da ANBIMA (payload com `titulos[]`);
- tabela gold possui `data_referencia`, `codigo_selic`, `tipo_correcao`, `index`, `data_validade`, `vna`, `vna_ajustado`;
- leitura via `read_data().vna.fetch_*`;
- atualização via `update(datasets=["vna"], ...)`;
- `force=True` reprocessa bronze/silver/gold para o escopo.

## Acceptance criteria

1. `vna` está em `PARTITION_SPECS`, `DATASETS` (10 datasets), bronze registry, silver registry, gold contracts, `MATERIALIZERS`, `BUILDER_TABLE` e persistence.
2. Nenhum skip hard-coded ligado ao placeholder impede o dataset/builder `vna` em `gold/tasks.py`, `gold/incremental.py` ou `pipeline_invalidation.py`.
3. `AnbimaClient.fetch_vna(date_iso)` existe e reutiliza `fetch_by_date(self.vna_url, date_iso)`.
4. Bronze grava payload bruto diário em `bronze/vna/data=YYYY-MM-DD/part.json`.
5. Silver produz DataFrame com colunas: `data_referencia`, `codigo_selic`, `tipo_correcao`, `index`, `data_validade`, `vna`.
6. Existe `src/app/database/migrations/012_vna.sql` com DDL completo de `VNA` + índice `idx_vna_data`.
7. `apply_migrations()` aplica versão `012` uma vez; `VNA` aparece em `BUSINESS_TABLES_V2` e no banco após migrate.
8. `TABLE_VNA` / `VNA_COLUMNS` definidos em `schema.py` e usados pelo repository.
9. Gold persiste `VNA` via repository usando upsert (sem `NotImplementedError`).
10. `read_data().vna.fetch_all/latest/on/range` funciona com os mesmos contratos dos datasets diários.
11. `update(datasets=["vna"], ...)` executa migrations (se pendente) + bronze → silver → gold somente para `vna`.
12. `update(..., datasets=["vna"], force=True, refresh_dates=[...])` invalida bronze/silver/gold da data e reprocessa.
13. `resolve_invalidation_scope(datasets=["vna"], ...)` inclui builder `vna` e partições diárias corretas.
14. `pytest tests/providers tests/contracts tests/database tests/public tests/services -q` passa; testes de invalidação e migration atualizados.

## Non-goals

- Não calcular preço de LFT.
- Não alterar regras de IPCA, BMF, CDI, PTAX ou mercado secundário.
- Não criar endpoint HTTP externo.
- Não modificar o contrato de `read_data()` além de adicionar o novo atributo `vna`.
- Não implementar fallback para outro provider.

## Reference files

Padrões úteis:

- Provider diário ANBIMA: `src/app/lake/bronze/extractors/mercado_secundario.py`
- Provider diário BCB: `src/app/lake/bronze/extractors/cdi.py`
- Silver diário simples: `src/app/lake/silver/transforms/cdi.py`, `src/app/lake/silver/transforms/ptax.py`
- Gold materializer simples: `src/app/lake/gold/materializers/cdi.py`, `src/app/lake/gold/materializers/ptax.py`
- Repository simples: `src/app/repositories/cdi.py`, `src/app/repositories/ptax.py`
- Migrations: `src/app/database/migrations/003_cdi.sql`, `src/app/database/migrate.py`, `tests/database/test_migrations_v2.py`
- Reader público: `src/app/database/readers/gold_reader.py`
- Force refresh: `src/app/services/pipeline_invalidation.py`
- Sync diário: `src/app/services/sync_runner.py`, `src/app/lake/gold/tasks.py`, `src/app/lake/gold/incremental.py`
- Scaffolding atual a remover: tabela [Scaffolding temporário](#scaffolding-temporário-a-remover)

## Ordem sugerida de implementação

Seguir `tasks.md`. Dependências críticas:

1. Task 1 (contratos) antes de bronze/silver tasks.
2. Tasks 2–4 (provider → bronze → silver) antes de gold materializer.
3. **Task 7 (migration `012_vna.sql` + schema + repository + `BUILDER_TABLE`)** antes de persistência, queries e E2E.
4. Task 5 (materializer) pode paralelizar com Task 7 após silver; Task 8/9 **dependem** da migration aplicada.
5. Task 10 (invalidação/sync scaffolding) antes de declarar FR-009/FR-011 concluídos.
6. Task 11 (E2E) por último.
