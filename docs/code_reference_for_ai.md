# Referência de código para IA

> Documento gerado para onboarding de outra IA. Contexto de arquitetura: [project_architecture_and_dependencies.md](project_architecture_and_dependencies.md). Estudo histórico (bronze antigo): [project_bronze_architecture_study.md](project_bronze_architecture_study.md).

## Como usar este documento

### Ordem de leitura
1. `app.config` → `app.contracts` → `app.core` → `app.providers`
2. `app.lake/bronze` → `app.lake/silver` → `app.lake/gold`
3. `run_bronze.py` / `run_silver.py` / `run_gold.py` → `tests/`

### Convenções
- `PYTHONPATH` inclui `src/`; imports canônicos: `from app.lake...`, `from app.config...`.
- Dados em `{DATA_ROOT}/raw` (bronze) e `{DATA_ROOT}/silver` (silver), Hive `partition_key=value`.

### O que o repositório NÃO faz hoje
- Cálculo de títulos (PU, taxa, DV01) — futuro `titulospub`, fora deste repo.
- API FastAPI / Dash — não implementados.
- Persistência SQL gold via repositories (stub INSERT); `run_gold` não grava ainda.

### Invariantes
- **Bronze:** raw fiel à fonte; 1 artefato por partição.
- **Silver:** schema canônico Parquet.
- **Gold:** saída pronta para INSERT (`DataFrame` ou `list[str]`); sem chamar providers.

### Arquivos sensíveis
- `app/lake/gold/builders/ipca_dict.py` — regras fiscais IPCA.
- Não copiar comportamento do `legacy/` sem diff explícito.

---

## Fluxos end-to-end

### 1. Bronze daily
`run_bronze.py` → `cmd_daily` → `resolve_bronze_tasks(end)` → `run_bronze_phase(tasks)` → para cada `DatasetTask`: `registry.extract_dataset(name, dates)` → extractor → `writer` → `ExtractResult`.

### 2. Silver one dataset
`run_silver.py` → `resolve_silver_tasks` → `run_silver_phase` → `read_bronze_partition` → `registry.get_transform(name).normalize_partition(df)` → `write_partition_parquet`.

### 3. Gold pass-through (CDI)
`GoldOrchestrator.materialize_cdi(dates)` → `read_silver` (partições diárias) → `registry.build` → `materializers/cdi.from_silver` → DataFrame `data_referencia, cdi`.

### 4. Gold ipca_dict (diário)
`materialize_ipca_dict(dates)` → `resolve_feriados_set` (gold ou silver) → `read_silver_range` mensal ipca+proj → para cada data `build_for_date` → `to_dataframe`. Regra `USA_FECHADO`: ref M-1 + antes do dia 15 útil + índices distintos.

### 5. Projeções bronze merge
`extract_projecoes` → API latest + meses candidatos → `flatten_projecoes_payload` → `merge_projecoes_records` por `data_coleta` → JSON em `reference_month=YYYY-MM-01`.

---

## Contratos de dados

### Partições (bronze/silver)

| dataset | partition_key | granularidade | artefato bronze |
|---------|---------------|---------------|-----------------|
| mercado_secundario | data | day | json |
| liquidacoes_mercado | data | day | parquet |
| ajustes_bmf | data | day | parquet |
| leiloes | data | day | json |
| ipca_indice | reference_month | month | parquet |
| feriados | snapshot | snapshot | parquet |
| projecoes | reference_month | month | json |
| cdi | data | day | parquet |
| ptax | data | day | parquet |

### Gold builders

| name | tipo | silver inputs | saída |
|------|------|---------------|-------|
| feriados..leiloes | materializer | 1 dataset | DataFrame ou list |
| ipca_dict | builder+materializer | ipca_indice, projecoes | DataFrame diário |
| vna_lft | stub | — | NotImplemented |

### Tipos (`contracts/`)
- `ExtractResult`, `BronzeResult`, `BronzeExtractor`
- `SilverResult`, `SilverTransform`, `SilverPartitionRef`
- Protocols em `contracts/providers.py`

---

## Índice por pacote

## `__init__.py/`

### `__init__.py`

**Papel:** Brazil fixed income analytics application package.
**Camada:** outros
**Importa (interno):** `app.config`
**Notas para IA:** reexporta API do pacote; ver imports no arquivo.

## `agents/__init__.py/`

### `agents/__init__.py`

**Papel:** (sem docstring de módulo)
**Camada:** outros
**Notas para IA:** reexporta API do pacote; ver imports no arquivo.

## `cli/__init__.py/`

### `cli/__init__.py`

**Papel:** Command-line interfaces for lake layers.
**Camada:** cli
**Notas para IA:** reexporta API do pacote; ver imports no arquivo.

## `cli/bronze.py/`

### `cli/bronze.py`

**Papel:** CLI for the hive-partitioned bronze layer.
**Camada:** cli
**Funções:** `_setup_logging, _print_results, cmd_init, cmd_daily, cmd_one, _backfill_tasks, cmd_backfill, main`
**Importa (interno):** `app.config`, `app.core.datasets`, `app.core.dates`, `app.core.partitioning`, `app.lake.bronze.incremental`, `app.lake.bronze.pipeline`, `app.lake.bronze.tasks`
**Importa (externo):** `logging`, `sys`

## `cli/gold.py/`

### `cli/gold.py`

**Papel:** CLI for gold materialization (no SQL persist yet).
**Camada:** cli
**Funções:** `_setup_logging, _print_materialized, _materialize_builder, cmd_init, cmd_one, cmd_backfill, main`
**Importa (interno):** `app.config`, `app.core.dates`, `app.lake.gold`, `app.lake.gold.contracts`
**Importa (externo):** `logging`, `pandas`, `sys`

## `cli/silver.py/`

### `cli/silver.py`

**Papel:** CLI for the hive-partitioned silver layer.
**Camada:** cli
**Funções:** `_setup_logging, _print_results, cmd_init, cmd_daily, cmd_one, _backfill_tasks, cmd_backfill, main`
**Importa (interno):** `app.config`, `app.core.datasets`, `app.core.dates`, `app.core.partitioning`, `app.lake.silver.pipeline`, `app.lake.silver.tasks`
**Importa (externo):** `logging`, `sys`

## `config/__init__.py/`

### `config/__init__.py`

**Papel:** Application configuration.
**Camada:** config
**Importa (interno):** `app.config.paths`, `app.config.settings`
**Notas para IA:** reexporta API do pacote; ver imports no arquivo.

## `config/paths.py/`

### `config/paths.py`

**Papel:** Project root and path resolution.
**Camada:** config
**Funções:** `resolve_path`

## `config/settings.py/`

### `config/settings.py`

**Papel:** Central configuration (Pydantic Settings per data source).
**Camada:** config
**Classes:** `PathSettings, AnbimaSettings, FeriadosSettings, BcbSettings, TesouroSettings, SidraSettings, UptodataSettings, AppSettings`
**Funções:** `_validate_iso_date, get_settings`
**Importa (interno):** `app.config.paths`
**Importa (externo):** `dotenv`, `logging`, `os`, `pydantic`, `pydantic_settings`

## `contracts/__init__.py/`

### `contracts/__init__.py`

**Papel:** Layer contracts (types and protocols only — no I/O).
**Camada:** contracts
**Importa (interno):** `app.contracts.bronze`, `app.contracts.providers`, `app.contracts.silver`
**Notas para IA:** reexporta API do pacote; ver imports no arquivo.

## `contracts/bronze.py/`

### `contracts/bronze.py`

**Papel:** Contracts for bronze pipeline extractors and orchestration.
**Camada:** contracts
**Classes:** `ExtractResult, BronzePartitionRef, BronzeResult`

## `contracts/providers.py/`

### `contracts/providers.py`

**Papel:** Contracts for raw data providers (fetch patterns, not a single mega-Protocol).
**Camada:** providers
**Classes:** `SidraIpcaProvider, AnbimaFeedClient`
**Importa (externo):** `pandas`

## `contracts/silver.py/`

### `contracts/silver.py`

**Papel:** Contracts for silver pipeline transforms and orchestration.
**Camada:** contracts
**Classes:** `SilverPartitionRef, SilverResult`
**Importa (externo):** `pandas`

## `core/__init__.py/`

### `core/__init__.py`

**Papel:** Shared domain utilities: dates, dataset registry, partition specs.
**Camada:** core
**Importa (interno):** `app.core.datasets`, `app.core.dates`, `app.core.exceptions`, `app.core.partitioning`
**Notas para IA:** reexporta API do pacote; ver imports no arquivo.

## `core/datasets.py/`

### `core/datasets.py`

**Papel:** Dataset registry metadata (date modes per pipeline).
**Camada:** core
**Classes:** `DatasetConfig`
**Funções:** `get_dataset_config`
**Importa (interno):** `app.core.partitioning`

## `core/dates.py/`

### `core/dates.py`

**Papel:** Date utilities for pipeline task resolution.
**Camada:** core
**Funções:** `iso_month_first, _month_start_from_iso, months_in_range, business_days`

## `core/exceptions.py/`

### `core/exceptions.py`

**Papel:** Shared pipeline exceptions (not layer contracts).
**Camada:** core
**Classes:** `PipelineError, DatasetNotFoundError, PartitionMissingError`

## `core/partitioning.py/`

### `core/partitioning.py`

**Papel:** Partition specs per dataset (hive keys and artifact format).
**Camada:** core
**Classes:** `DatasetPartitionSpec`
**Funções:** `get_partition_spec, is_snapshot_dataset`

## `database/__init__.py/`

### `database/__init__.py`

**Papel:** Database connection and migrations.
**Camada:** database
**Importa (interno):** `app.database.connection`, `app.database.migrate`, `app.database.schema`
**Notas para IA:** reexporta API do pacote; ver imports no arquivo.

## `database/connection.py/`

### `database/connection.py`

**Papel:** SQLite connection helpers.
**Camada:** database
**Funções:** `get_connection, execute_script, execute`
**Importa (interno):** `app.config`
**Importa (externo):** `sqlite3`

## `database/migrate.py/`

### `database/migrate.py`

**Papel:** Apply versioned SQL migrations (ported from legacy rf_lake).
**Camada:** database
**Classes:** `Migration`
**Funções:** `_ensure_table, _applied, _list_files, apply_migrations`
**Importa (interno):** `app.database.connection`
**Importa (externo):** `sqlite3`

## `database/schema.py/`

### `database/schema.py`

**Papel:** Gold table names and column metadata.
**Camada:** database
**Importa (interno):** `app.lake.gold.materializers.ipca_dict`

## `lake/__init__.py/`

### `lake/__init__.py`

**Papel:** Data lake layers (bronze / silver / gold).
**Camada:** outros
**Notas para IA:** reexporta API do pacote; ver imports no arquivo.

## `lake/bronze/`

### `lake/bronze/__init__.py`

**Papel:** Bronze pipeline: raw hive-partitioned artifacts.
**Camada:** bronze
**Funções:** `__getattr__`
**Importa (interno):** `app.contracts`, `app.core.partitioning`, `app.lake.bronze.extract_dataset`, `app.lake.bronze.pipeline`, `app.lake.bronze.reader`, `app.lake.bronze.registry`, `app.lake.bronze.tasks`
**Notas para IA:** reexporta API do pacote; ver imports no arquivo.

### `lake/bronze/_extract_json.py`

**Papel:** Shared JSON partition extract loop (internal).
**Camada:** bronze
**Funções:** `extract_json_partitions`
**Importa (interno):** `app.contracts`, `app.core.partitioning`, `app.lake.bronze.incremental`, `app.lake.bronze.writer`

### `lake/bronze/_split.py`

**Papel:** Date helpers for hive partitioning only (no canonical schema).
**Camada:** bronze
**Funções:** `pick_date_column, to_iso_date_string, partition_values_from_series, split_dataframe_by_partition, iso_month_from_mes_ano, months_from_candidate_dates, auction_date_from_record`
**Importa (interno):** `app.core.dates`
**Importa (externo):** `pandas`

### `lake/bronze/extract_dataset.py`

**Papel:** Public entry point for bronze extraction.
**Camada:** bronze
**Funções:** `extract_dataset`
**Importa (interno):** `app.contracts`, `app.lake.bronze.registry`

### `lake/bronze/extractors/__init__.py`

**Papel:** Per-dataset bronze extractors.
**Camada:** bronze
**Notas para IA:** reexporta API do pacote; ver imports no arquivo.

### `lake/bronze/extractors/_projecoes_split.py`

**Papel:** Flatten/merge JSON projeções ANBIMA por reference_month.
**Camada:** bronze
**Funções:** `flatten_projecoes_payload, mes_referencia_to_partition_key, group_records_by_reference_month, _record_dedup_key, merge_projecoes_records, load_partition_records, write_merged_partition, _active_calendar_month_keys, partitions_to_refresh_projecoes, partition_key_to_mes_ano`
**Importa (interno):** `app.lake.bronze.incremental`, `app.lake.bronze.paths`, `app.lake.bronze.writer`
**Importa (externo):** `json`, `re`
**Chamado por:** extractors/projecoes.py
**Notas para IA:** Partição = mes_referencia do dado, não mês da consulta API.

### `lake/bronze/extractors/ajustes_bmf.py`

**Papel:** Bronze: UpToData BMF adjustments (raw parquet per day).
**Camada:** bronze
**Funções:** `extract_ajustes_bmf`
**Importa (interno):** `app.contracts`, `app.core.partitioning`, `app.lake.bronze._split`, `app.lake.bronze.incremental`, `app.lake.bronze.writer`, `app.providers.uptodata`

### `lake/bronze/extractors/cdi.py`

**Papel:** Bronze: ANBIMA SELIC estimate (raw parquet per day).
**Camada:** bronze
**Funções:** `extract_cdi`
**Importa (interno):** `app.contracts`, `app.core.partitioning`, `app.lake.bronze._split`, `app.lake.bronze.incremental`, `app.lake.bronze.writer`, `app.providers.anbima`
**Importa (externo):** `pandas`

### `lake/bronze/extractors/feriados.py`

**Papel:** Bronze: national holidays snapshot (raw XLS as parquet).
**Camada:** bronze
**Funções:** `extract_feriados`
**Importa (interno):** `app.contracts`, `app.core.partitioning`, `app.lake.bronze.incremental`, `app.lake.bronze.writer`, `app.providers.feriados`
**Importa (externo):** `pandas`

### `lake/bronze/extractors/ipca_indice.py`

**Papel:** Bronze: SIDRA IPCA table (raw sidrapy parquet per reference month).
**Camada:** bronze
**Funções:** `_allowed_months, extract_ipca_indice`
**Importa (interno):** `app.config`, `app.contracts`, `app.core.dates`, `app.core.partitioning`, `app.lake.bronze._split`, `app.lake.bronze.incremental`, `app.lake.bronze.writer`, `app.providers.sidra`

### `lake/bronze/extractors/leiloes.py`

**Papel:** Bronze: Tesouro auction results (raw JSON list per auction day).
**Camada:** bronze
**Funções:** `extract_leiloes`
**Importa (interno):** `app.contracts`, `app.core.partitioning`, `app.lake.bronze._split`, `app.lake.bronze.incremental`, `app.lake.bronze.writer`, `app.providers.tesouro`

### `lake/bronze/extractors/liquidacoes_mercado.py`

**Papel:** Bronze: BCB NegE settlements (raw parquet per day).
**Camada:** bronze
**Funções:** `extract_liquidacoes_mercado`
**Importa (interno):** `app.contracts`, `app.core.partitioning`, `app.lake.bronze._split`, `app.lake.bronze.incremental`, `app.lake.bronze.writer`, `app.providers.bcb`

### `lake/bronze/extractors/mercado_secundario.py`

**Papel:** Bronze: ANBIMA mercado secundário TPF (raw JSON per day).
**Camada:** bronze
**Funções:** `extract_mercado_secundario`
**Importa (interno):** `app.contracts`, `app.core.partitioning`, `app.lake.bronze._extract_json`, `app.providers.anbima`

### `lake/bronze/extractors/projecoes.py`

**Papel:** Bronze: ANBIMA projections (JSON per reference_month, split by mes_referencia).
**Camada:** bronze
**Funções:** `_candidate_months, extract_projecoes`
**Importa (interno):** `app.contracts`, `app.core.dates`, `app.core.partitioning`, `app.lake.bronze._split`, `app.lake.bronze.extractors._projecoes_split`, `app.lake.bronze.paths`, `app.providers.anbima`

### `lake/bronze/extractors/ptax.py`

**Papel:** Bronze: BCB PTAX USD closing rates (raw parquet per day).
**Camada:** bronze
**Funções:** `extract_ptax`
**Importa (interno):** `app.contracts`, `app.core.partitioning`, `app.lake.bronze._split`, `app.lake.bronze.incremental`, `app.lake.bronze.writer`, `app.providers`

### `lake/bronze/incremental.py`

**Papel:** Incremental bronze loads based on hive partition presence.
**Camada:** bronze
**Funções:** `missing_partition_values`
**Importa (interno):** `app.core.partitioning`, `app.lake.bronze.reader`, `app.lake.bronze.storage`

### `lake/bronze/partitioning.py`

**Papel:** Shim: use ``core.partitioning`` (deprecated path ``lake.bronze.partitioning``).
**Camada:** bronze
**Importa (interno):** `app.core.partitioning`

### `lake/bronze/paths.py`

**Papel:** Hive-style paths under the bronze (raw) layer.
**Camada:** bronze
**Funções:** `get_bronze_root, bronze_dataset_dir, bronze_partition_dir, bronze_partition_path`
**Importa (interno):** `app.config`

### `lake/bronze/pipeline.py`

**Papel:** Bronze pipeline orchestration.
**Camada:** bronze
**Funções:** `run_bronze, run_bronze_phase`
**Importa (interno):** `app.config`, `app.contracts`, `app.lake.bronze.registry`, `app.lake.bronze.tasks`
**Importa (externo):** `logging`

### `lake/bronze/reader.py`

**Papel:** Hive-partitioned bronze reader (symmetric to writer.py).
**Camada:** bronze
**Funções:** `_partition_column_name, _load_json_artifact, _load_artifact, list_partition_values, partition_values_for_range, _partition_ref, iter_partitions_in_range, read_partition, read_partitions, read_range`
**Importa (interno):** `app.contracts`, `app.core.dates`, `app.core.partitioning`, `app.lake.bronze.paths`, `app.lake.bronze.storage`
**Importa (externo):** `json`, `pandas`

### `lake/bronze/registry.py`

**Papel:** Bronze extractor registry.
**Camada:** bronze
**Funções:** `extract_dataset`
**Importa (interno):** `app.contracts`, `app.lake.bronze.extractors.ajustes_bmf`, `app.lake.bronze.extractors.cdi`, `app.lake.bronze.extractors.feriados`, `app.lake.bronze.extractors.ipca_indice`, `app.lake.bronze.extractors.leiloes`, `app.lake.bronze.extractors.liquidacoes_mercado`, `app.lake.bronze.extractors.mercado_secundario`, `app.lake.bronze.extractors.projecoes`, `app.lake.bronze.extractors.ptax`

### `lake/bronze/storage.py`

**Papel:** Bronze artifact presence checks (shared by writer, reader, incremental).
**Camada:** bronze
**Funções:** `partition_artifact_exists`
**Importa (interno):** `app.lake.bronze.paths`

### `lake/bronze/tasks.py`

**Papel:** Bronze task resolution (partition-aware date lists per dataset).
**Camada:** bronze
**Classes:** `DatasetTask`
**Funções:** `_dates_for_dataset, resolve_bronze_tasks`
**Importa (interno):** `app.config`, `app.core.datasets`, `app.core.dates`, `app.core.partitioning`, `app.lake.bronze.incremental`

### `lake/bronze/writer.py`

**Papel:** Write raw bronze artifacts into hive partitions (no schema normalization).
**Camada:** bronze
**Funções:** `ensure_partition_dir, write_raw_json, write_raw_parquet, write_partition_json, write_partition_parquet, write_dataframe_partitions`
**Importa (interno):** `app.core.partitioning`, `app.lake.bronze._split`, `app.lake.bronze.paths`, `app.lake.bronze.storage`
**Importa (externo):** `json`, `pandas`

## `lake/gold/`

### `lake/gold/__init__.py`

**Papel:** Gold layer: silver → builders → gold-ready objects (pipeline-driven).
**Camada:** gold
**Importa (interno):** `app.lake.gold`, `app.lake.gold.contracts`, `app.lake.gold.orchestrator`
**Notas para IA:** reexporta API do pacote; ver imports no arquivo.

### `lake/gold/_feriados_source.py`

**Papel:** Read persisted gold holidays (FERIADOS). Empty until SQL gold layer is wired.
**Camada:** gold
**Funções:** `read_feriados_gold`

### `lake/gold/_io.py`

**Papel:** Silver read helpers — sole entry point from gold to lake.silver.reader.
**Camada:** gold
**Funções:** `read_silver_range, read_silver_partition, read_silver_partitions, iter_silver_partitions_in_range, list_silver_partition_values`
**Importa (interno):** `app.contracts`, `app.lake.silver.reader`
**Importa (externo):** `pandas`

### `lake/gold/builders/__init__.py`

**Papel:** Gold builders — transforms silver into domain objects (feriados uses materializers/).
**Camada:** gold
**Importa (interno):** `app.lake.gold.builders`
**Notas para IA:** reexporta API do pacote; ver imports no arquivo.

### `lake/gold/builders/anbimas.py`

**Papel:** Future: build ANBIMA titulos dict from silver dataset ``mercado_secundario``.
**Camada:** gold

### `lake/gold/builders/base.py`

**Papel:** Shared helpers for gold builders (phase B).
**Camada:** gold
**Funções:** `resolve_as_of_date, require_dataset`
**Importa (interno):** `app.lake.gold.contracts`
**Importa (externo):** `pandas`

### `lake/gold/builders/bmf.py`

**Papel:** Future: build BMF DI/DAP dict from silver dataset ``ajustes_bmf``.
**Camada:** gold

### `lake/gold/builders/cdi.py`

**Papel:** Future: build CDI series from silver dataset ``cdi`` (columns data_referencia, cdi).
**Camada:** gold

### `lake/gold/builders/ipca_dict.py`

**Papel:** Regras de negócio IPCA diário (projeção, fechado, dia 15 útil).
**Camada:** gold
**Funções:** `_month_start, _ref_month_column, slice_monthly_frames, e_dia_util, adicionar_dias_uteis, inicio_fim_mes_ipca, projecao_mais_recente, projecao_mais_recente_valor, ipca_fechado_from_monthly, dicionario_ipca, build_for_date`
**Importa (externo):** `pandas`
**Chamado por:** registry._build_ipca_dict
**Notas para IA:** Não alterar fórmulas sem validação vs legado/notebook.

### `lake/gold/builders/vna_lft.py`

**Papel:** Future: build VNA LFT after bronze/silver dataset for ANBIMA VNA exists.
**Camada:** gold

### `lake/gold/contracts.py`

**Papel:** Gold layer contracts: builder names, silver inputs, pipeline context.
**Camada:** gold
**Classes:** `BuilderContext, GoldMaterialized`
**Funções:** `is_snapshot_only_builder`
**Importa (interno):** `app.core.partitioning`
**Importa (externo):** `pandas`

### `lake/gold/materializers/__init__.py`

**Papel:** Gold pass-through materializers (silver already in final shape).
**Camada:** gold
**Importa (interno):** `app.lake.gold.materializers.feriados`
**Notas para IA:** reexporta API do pacote; ver imports no arquivo.

### `lake/gold/materializers/_tabular.py`

**Papel:** Shared helpers for tabular pass-through materializers.
**Camada:** gold
**Funções:** `prepare_tabular_output`
**Importa (externo):** `pandas`

### `lake/gold/materializers/bmf.py`

**Papel:** BMF ajustes: silver partitions → DataFrame ready for SQL INSERT.
**Camada:** gold
**Funções:** `from_silver`
**Importa (interno):** `app.lake.gold.contracts`
**Importa (externo):** `pandas`

### `lake/gold/materializers/cdi.py`

**Papel:** CDI: silver partitions → DataFrame ready for SQL INSERT.
**Camada:** gold
**Funções:** `from_silver`
**Importa (interno):** `app.lake.gold.contracts`
**Importa (externo):** `pandas`

### `lake/gold/materializers/feriados.py`

**Papel:** Feriados: silver snapshot → list of ISO dates for FERIADOS SQL.
**Camada:** gold
**Funções:** `from_silver`
**Importa (interno):** `app.lake.gold.contracts`

### `lake/gold/materializers/ipca_dict.py`

**Papel:** IPCA dict: builder dicts → DataFrame ready for SQL INSERT.
**Camada:** gold
**Funções:** `_row_from_dict, to_dataframe`
**Importa (externo):** `pandas`

### `lake/gold/materializers/leiloes.py`

**Papel:** Leilões: silver partitions → DataFrame ready for SQL INSERT (LEILOES).
**Camada:** gold
**Funções:** `from_silver`
**Importa (interno):** `app.lake.gold.contracts`, `app.lake.gold.materializers._tabular`
**Importa (externo):** `pandas`

### `lake/gold/materializers/liquidacoes_mercado.py`

**Papel:** Liquidações mercado: silver partitions → DataFrame ready for SQL INSERT.
**Camada:** gold
**Funções:** `from_silver`
**Importa (interno):** `app.lake.gold.contracts`, `app.lake.gold.materializers._tabular`
**Importa (externo):** `pandas`

### `lake/gold/materializers/mercado_secundario.py`

**Papel:** Mercado secundário: silver partitions → DataFrame ready for SQL INSERT.
**Camada:** gold
**Funções:** `from_silver`
**Importa (interno):** `app.lake.gold.contracts`, `app.lake.gold.materializers._tabular`
**Importa (externo):** `pandas`

### `lake/gold/materializers/ptax.py`

**Papel:** PTAX USD: silver partitions → DataFrame ready for SQL INSERT.
**Camada:** gold
**Funções:** `from_silver`
**Importa (interno):** `app.lake.gold.contracts`
**Importa (externo):** `pandas`

### `lake/gold/orchestrator.py`

**Papel:** Orquestra leitura silver e materialização gold (pass-through e builders).
**Camada:** gold
**Classes:** `GoldOrchestrator`
**Importa (interno):** `app.core.partitioning`, `app.lake.gold`, `app.lake.gold._feriados_source`, `app.lake.gold._io`, `app.lake.gold.contracts`, `app.lake.silver.storage`
**Importa (externo):** `pandas`
**Chamado por:** notebooks, futuro run_gold.py, testes
**Notas para IA:** ipca_dict usa janela mensal, não ctx.dates como partição diária.

### `lake/gold/registry.py`

**Papel:** Dispatch silver frames to materializers (pass-through) or builders (transform).
**Camada:** gold
**Funções:** `_build_ipca_dict, build`
**Importa (interno):** `app.lake.gold.builders.ipca_dict`, `app.lake.gold.contracts`, `app.lake.gold.materializers.bmf`, `app.lake.gold.materializers.cdi`, `app.lake.gold.materializers.feriados`, `app.lake.gold.materializers.ipca_dict`, `app.lake.gold.materializers.leiloes`, `app.lake.gold.materializers.liquidacoes_mercado`, `app.lake.gold.materializers.mercado_secundario`, `app.lake.gold.materializers.ptax`

## `lake/silver/`

### `lake/silver/__init__.py`

**Papel:** Silver layer: normalize bronze hive partitions to canonical parquet.
**Camada:** silver
**Importa (interno):** `app.lake.silver.pipeline`, `app.lake.silver.tasks`
**Notas para IA:** reexporta API do pacote; ver imports no arquivo.

### `lake/silver/expand.py`

**Papel:** Expand monthly silver/bronze partitions to business-day grain at read time.
**Camada:** silver
**Funções:** `_month_key, read_monthly_as_daily`
**Importa (interno):** `app.core.dates`, `app.core.partitioning`, `app.lake.bronze.reader`, `app.lake.silver.reader`
**Importa (externo):** `pandas`

### `lake/silver/incremental.py`

**Papel:** Incremental silver loads: bronze present and silver missing or stale.
**Camada:** silver
**Funções:** `_bronze_newer_than_silver, missing_silver_partitions`
**Importa (interno):** `app.core.partitioning`, `app.lake.bronze.paths`, `app.lake.silver.paths`, `app.lake.silver.reader`, `app.lake.silver.storage`

### `lake/silver/mappers/anbima_projecoes.py`

**Papel:** Map ANBIMA projection payloads to flat DataFrames.
**Camada:** silver
**Funções:** `projecoes_to_df`
**Importa (externo):** `pandas`

### `lake/silver/mappers/sidra_ipca.py`

**Papel:** Map raw SIDRA (sidrapy) tables into canonical IPCA long format.
**Camada:** silver
**Funções:** `_find_header_row, _sidra_abbreviated_to_long, sidra_ipca_to_long`
**Importa (externo):** `pandas`

### `lake/silver/mappers/uptodata.py`

**Papel:** UpToData BMF row filters (port of legacy uptodata.mapping).
**Camada:** silver
**Funções:** `filtro_di_dap`
**Importa (externo):** `pandas`

### `lake/silver/normalize.py`

**Papel:** Shared normalization helpers for silver ETL (port of legacy rf_lake.silver.normalize).
**Camada:** silver
**Funções:** `normalize_numeric_columns, normalize_date_columns, remove_duplicate_columns`
**Importa (externo):** `pandas`

### `lake/silver/paths.py`

**Papel:** Hive-style paths under the silver layer.
**Camada:** silver
**Funções:** `get_silver_root, silver_dataset_dir, silver_partition_dir, silver_partition_path`
**Importa (interno):** `app.config`

### `lake/silver/pipeline.py`

**Papel:** Silver pipeline: bronze partition → normalize → hive silver parquet.
**Camada:** silver
**Funções:** `_process_partition, run_silver, run_silver_phase`
**Importa (interno):** `app.config`, `app.contracts`, `app.core.partitioning`, `app.lake.bronze.extractors._projecoes_split`, `app.lake.bronze.reader`, `app.lake.silver.incremental`, `app.lake.silver.paths`, `app.lake.silver.registry`, `app.lake.silver.tasks`, `app.lake.silver.transforms.projecoes`, `app.lake.silver.writer`
**Importa (externo):** `logging`

### `lake/silver/reader.py`

**Papel:** Hive-partitioned silver reader (symmetric to bronze reader).
**Camada:** silver
**Funções:** `_partition_column_name, list_partition_values, partition_values_for_range, _partition_ref, iter_partitions_in_range, read_partition, read_partitions, read_range`
**Importa (interno):** `app.contracts`, `app.core.dates`, `app.core.partitioning`, `app.lake.silver.paths`, `app.lake.silver.storage`
**Importa (externo):** `pandas`

### `lake/silver/registry.py`

**Papel:** Silver transform registry (dataset → normalize_partition).
**Camada:** silver
**Funções:** `get_transform`
**Importa (interno):** `app.contracts`, `app.lake.silver.transforms`

### `lake/silver/schemas.py`

**Papel:** Canonical silver column layouts and rename maps (port of legacy contracts + schema).
**Camada:** silver

### `lake/silver/storage.py`

**Papel:** Silver artifact presence checks.
**Camada:** silver
**Funções:** `partition_artifact_exists, bronze_exists`
**Importa (interno):** `app.lake.bronze.storage`, `app.lake.silver.paths`

### `lake/silver/tasks.py`

**Papel:** Silver task resolution: candidates in range where bronze exists and silver is missing.
**Camada:** silver
**Funções:** `resolve_silver_tasks`
**Importa (interno):** `app.config`, `app.core.datasets`, `app.core.dates`, `app.core.partitioning`, `app.lake.bronze.tasks`, `app.lake.silver.incremental`

### `lake/silver/transforms/__init__.py`

**Papel:** Per-dataset silver normalizers.
**Camada:** silver
**Notas para IA:** reexporta API do pacote; ver imports no arquivo.

### `lake/silver/transforms/ajustes_bmf.py`

**Papel:** (sem docstring de módulo)
**Camada:** silver
**Funções:** `normalize_partition`
**Importa (interno):** `app.lake.silver.mappers.uptodata`, `app.lake.silver.normalize`, `app.lake.silver.schemas`
**Importa (externo):** `pandas`

### `lake/silver/transforms/cdi.py`

**Papel:** (sem docstring de módulo)
**Camada:** silver
**Funções:** `normalize_partition`
**Importa (interno):** `app.lake.silver.normalize`, `app.lake.silver.schemas`
**Importa (externo):** `pandas`

### `lake/silver/transforms/feriados.py`

**Papel:** Holiday normalization to a single `data` column (YYYY-MM-DD).
**Camada:** silver
**Funções:** `normalize_partition, _normalize`
**Importa (externo):** `pandas`

### `lake/silver/transforms/ipca_indice.py`

**Papel:** (sem docstring de módulo)
**Camada:** silver
**Funções:** `ipca_long_to_monthly, normalize_partition`
**Importa (interno):** `app.lake.silver.mappers.sidra_ipca`
**Importa (externo):** `pandas`

### `lake/silver/transforms/leiloes.py`

**Papel:** (sem docstring de módulo)
**Camada:** silver
**Funções:** `normalize_partition`
**Importa (interno):** `app.lake.silver.normalize`, `app.lake.silver.schemas`
**Importa (externo):** `pandas`

### `lake/silver/transforms/liquidacoes_mercado.py`

**Papel:** (sem docstring de módulo)
**Camada:** silver
**Funções:** `normalize_partition`
**Importa (interno):** `app.lake.silver.normalize`, `app.lake.silver.schemas`
**Importa (externo):** `pandas`

### `lake/silver/transforms/mercado_secundario.py`

**Papel:** (sem docstring de módulo)
**Camada:** silver
**Funções:** `normalize_partition`
**Importa (interno):** `app.lake.silver.normalize`, `app.lake.silver.schemas`
**Importa (externo):** `pandas`

### `lake/silver/transforms/projecoes.py`

**Papel:** (sem docstring de módulo)
**Camada:** silver
**Funções:** `ref_month_to_iso, normalize_from_records, normalize_partition`
**Importa (interno):** `app.lake.silver.mappers.anbima_projecoes`, `app.lake.silver.normalize`, `app.lake.silver.schemas`
**Importa (externo):** `pandas`, `re`

### `lake/silver/transforms/ptax.py`

**Papel:** (sem docstring de módulo)
**Camada:** silver
**Funções:** `normalize_partition`
**Importa (interno):** `app.lake.silver.normalize`, `app.lake.silver.schemas`
**Importa (externo):** `pandas`

### `lake/silver/writer.py`

**Papel:** Write normalized silver artifacts into hive partitions.
**Camada:** silver
**Funções:** `ensure_partition_dir, write_raw_parquet, write_partition_parquet`
**Importa (interno):** `app.core.partitioning`, `app.lake.silver.paths`
**Importa (externo):** `pandas`

## `providers/__init__.py/`

### `providers/__init__.py`

**Papel:** External data providers: HTTP clients and file readers grouped by source.
**Camada:** providers
**Importa (interno):** `app.providers.anbima`, `app.providers.bcb`, `app.providers.feriados`, `app.providers.sidra`, `app.providers.tesouro`, `app.providers.uptodata`
**Notas para IA:** reexporta API do pacote; ver imports no arquivo.

## `providers/anbima/`

### `providers/anbima/__init__.py`

**Papel:** (sem docstring de módulo)
**Camada:** providers
**Importa (interno):** `app.providers.anbima.auth`, `app.providers.anbima.client`, `app.providers.anbima.estimativa_selic`
**Notas para IA:** reexporta API do pacote; ver imports no arquivo.

### `providers/anbima/auth.py`

**Papel:** OAuth2 authentication for the ANBIMA API.
**Camada:** providers
**Classes:** `Token, AnbimaAuth`
**Importa (interno):** `app.config`
**Importa (externo):** `base64`, `requests`, `time`

### `providers/anbima/client.py`

**Papel:** HTTP client for the ANBIMA API.
**Camada:** providers
**Classes:** `AnbimaClient`
**Funções:** `_meses_anos_range`
**Importa (interno):** `app.config`, `app.providers.anbima.auth`
**Importa (externo):** `requests`, `time`

### `providers/anbima/estimativa_selic.py`

**Papel:** ANBIMA daily SELIC rate estimate feed.
**Camada:** providers
**Funções:** `_payload_to_records, fetch_estimativa_selic`
**Importa (interno):** `app.config`, `app.providers.anbima.client`
**Importa (externo):** `pandas`

## `providers/base.py/`

### `providers/base.py`

**Papel:** Shared helpers for data providers.
**Camada:** providers
**Funções:** `ensure_date`

## `providers/bcb/`

### `providers/bcb/__init__.py`

**Papel:** (sem docstring de módulo)
**Camada:** providers
**Importa (interno):** `app.providers.bcb.cdi`, `app.providers.bcb.client`, `app.providers.bcb.ptax`, `app.providers.bcb.sgs`
**Notas para IA:** reexporta API do pacote; ver imports no arquivo.

### `providers/bcb/cdi.py`

**Papel:** CDI daily rate from BCB SGS (series 11 by default).
**Camada:** providers
**Funções:** `fetch_cdi_daily`
**Importa (interno):** `app.config`, `app.providers.base`, `app.providers.bcb.sgs`
**Importa (externo):** `pandas`

### `providers/bcb/client.py`

**Papel:** Client for BCB (Brazilian Central Bank) trade settlement files.
**Camada:** providers
**Funções:** `format_ano_mes, build_negociacoes_url, fetch_negociacoes_bruto_por_datas`
**Importa (interno):** `app.config`, `app.providers.base`
**Importa (externo):** `logging`, `pandas`

### `providers/bcb/ptax.py`

**Papel:** BCB PTAX closing rates (CSV export from ptax.bcb.gov.br).
**Camada:** providers
**Funções:** `_format_bcb_dmy, _add_years, _split_period_in_year_chunks, build_ptax_fechamento_url, _fetch_csv_text, _normalize_decimal_series, _is_html_response, _extract_ptax_csv_body, _csv_text_to_dataframe, fetch_ptax_fechamento, fetch_ptax_usd`
**Importa (interno):** `app.config`, `app.providers.base`
**Importa (externo):** `io`, `logging`, `pandas`, `re`, `requests`, `time`, `urllib`

### `providers/bcb/sgs.py`

**Papel:** BCB SGS (Sistema Gerenciador de Séries Temporais) JSON API client.
**Camada:** providers
**Funções:** `_format_bcb_dmy, _add_years, _split_period_in_10y_chunks, build_sgs_url, _replace_url_dates, _fetch_chunk_json, _records_to_dataframe, fetch_bcb_sgs_series`
**Importa (interno):** `app.config`, `app.providers.base`
**Importa (externo):** `logging`, `pandas`, `requests`, `time`, `urllib`

## `providers/feriados/`

### `providers/feriados/__init__.py`

**Papel:** (sem docstring de módulo)
**Camada:** providers
**Importa (interno):** `app.providers.feriados.client`
**Notas para IA:** reexporta API do pacote; ver imports no arquivo.

### `providers/feriados/client.py`

**Papel:** Client for national holidays (public ANBIMA XLS).
**Camada:** providers
**Funções:** `fetch_feriados`
**Importa (interno):** `app.config`
**Importa (externo):** `io`, `pandas`, `requests`

## `providers/sidra/`

### `providers/sidra/__init__.py`

**Papel:** (sem docstring de módulo)
**Camada:** providers
**Importa (interno):** `app.providers.sidra.client`
**Notas para IA:** reexporta API do pacote; ver imports no arquivo.

### `providers/sidra/client.py`

**Papel:** SIDRA (IBGE) client using sidrapy.
**Camada:** providers
**Classes:** `SidraIpcaClient`
**Importa (interno):** `app.config`
**Importa (externo):** `logging`, `pandas`, `sidrapy`, `time`

## `providers/tesouro/`

### `providers/tesouro/__init__.py`

**Papel:** (sem docstring de módulo)
**Camada:** providers
**Importa (interno):** `app.providers.tesouro.client`
**Notas para IA:** reexporta API do pacote; ver imports no arquivo.

### `providers/tesouro/client.py`

**Papel:** Client for National Treasury auction results API.
**Camada:** providers
**Funções:** `to_dd_mm_yyyy, get_resultados, get_resultados_by_dates`
**Importa (interno):** `app.config`
**Importa (externo):** `logging`, `requests`, `time`

## `providers/uptodata/`

### `providers/uptodata/__init__.py`

**Papel:** (sem docstring de módulo)
**Camada:** providers
**Importa (interno):** `app.providers.uptodata.client`
**Notas para IA:** reexporta API do pacote; ver imports no arquivo.

### `providers/uptodata/client.py`

**Papel:** UpToData client (local CSV files).
**Camada:** providers
**Funções:** `_resolve_uptodata_paths, definir_caminho_adj_bmf, scrap_ajustes_bmf, scrap_ajustes_bmf_for_dates`
**Importa (interno):** `app.config`
**Importa (externo):** `logging`, `os`, `pandas`, `traceback`

## `repositories/__init__.py/`

### `repositories/__init__.py`

**Papel:** Gold table repositories.
**Camada:** outros
**Importa (interno):** `app.repositories.base`, `app.repositories.ipca_dict`
**Notas para IA:** reexporta API do pacote; ver imports no arquivo.

## `repositories/base.py/`

### `repositories/base.py`

**Papel:** Repository protocol for gold SQL persistence.
**Camada:** outros
**Classes:** `Repository`
**Importa (externo):** `pandas`

## `repositories/ipca_dict.py/`

### `repositories/ipca_dict.py`

**Papel:** IPCA_DICT repository (stub — validates columns, no INSERT yet).
**Camada:** outros
**Classes:** `IpcaDictRepository`
**Funções:** `get_ipca_dict_repository`
**Importa (interno):** `app.database.schema`, `app.repositories.base`
**Importa (externo):** `logging`, `pandas`

## `services/__init__.py/`

### `services/__init__.py`

**Papel:** Application services — facades over lake gold (no provider calls).
**Camada:** outros
**Importa (interno):** `app.services.ipca`, `app.services.market_data`
**Notas para IA:** reexporta API do pacote; ver imports no arquivo.

## `services/ipca.py/`

### `services/ipca.py`

**Papel:** IPCA facade — delegates to gold builder (no duplicated business rules).
**Camada:** outros
**Funções:** `build_ipca_dict_for_date`
**Importa (interno):** `app.lake.gold.builders.ipca_dict`
**Importa (externo):** `pandas`

## `services/market_data.py/`

### `services/market_data.py`

**Papel:** Market data facade (placeholder for CDI, PTAX, etc. via gold).
**Camada:** outros
**Funções:** `get_orchestrator`
**Importa (interno):** `app.lake.gold`

## `services/rates.py/`

### `services/rates.py`

**Papel:** Rates facade (placeholder for future rate curves and indices).
**Camada:** outros

## Entrypoints (raiz do repo)

### `run_bronze.py`
**Papel:** CLI bronze: init, daily, one, backfill.
**Chama:** `resolve_bronze_tasks`, `run_bronze`, `run_bronze_phase`, `missing_partition_values`.

### `run_silver.py`
**Papel:** CLI silver: init, daily, one, backfill.
**Chama:** `resolve_silver_tasks`, `run_silver`, `run_silver_phase`.

### `run_gold.py`
**Papel:** CLI gold: init, one, backfill (sem INSERT SQL).

### `src/main.py`
**Papel:** `rf-analytics` dispatcher: bronze|silver|gold|migrate.

## Testes (`tests/`)

Rodar: `pytest tests/ -q`. Gold: `pytest tests/lake/gold/ -q`.

| Teste | Garante |
|-------|---------|
| test_ipca_dict_builder | USA_FECHADO, slice mensal |
| test_ipca_dict_orchestrator | feriados fallback, materialize |
| test_leiloes_materializer | datas esparsas, dedup |
| test_*_materializer (gold) | colunas SQL, filtros dates |
| test_*_extractor (bronze) | extractors por fonte |
| test_silver_pipeline | bronze→silver |

## Legacy

`legacy/rf_lake/` — monólito Bronze/Silver/Gold + SQLite. Equivalência: bronze→`app/lake/bronze`, silver→`app/lake/silver`, gold SQL→`app/database/` + `app/repositories/`.

## Notebooks

`notebooks/test_gold.ipynb` — protótipo; produção em `src/app/lake/gold/`.
