# Feature Spec — `update(force=True)` com refresh destrutivo bronze → silver → gold

## Feature Name

`005-force-refresh-pipeline`

## Status and dependencies

- **Prerequisites (completed):** `001-public-database-api`, `002-import-alias-brazilian-bonds-db`, `003-public-gold-reader-api`
- **Motivação:** partições bronze/silver existentes impedem reextração (ex.: `ajustes_bmf` em `2026-05-25` sem DAP após CSV incompleto); `force=True` atual só dispara sync sem invalidar artefatos
- **Scope:** novo comportamento de `update(force=True)` e parâmetros associados; invalidação seletiva por `datasets` e janela de datas
- **Out of scope:** `read_data(force=...)` (permanece somente leitura); PostgreSQL; mudança de fórmulas financeiras; reprocessar lake fora do `data_root` ativo

## Objective

Quando o consumidor chamar **`update(..., force=True)`**, o pacote deve **invalidar e reconstruir** os dados nas camadas **bronze, silver e gold (SQLite)** para o escopo solicitado, em vez de apenas pular partições “já existentes”.

O comportamento aplica-se a **todos os datasets e builders do pipeline** (não apenas `ajustes_bmf` / BMF). `ajustes_bmf` é o caso motivador documentado, mas a implementação deve ser genérica.

Após o refresh, `read_data()` deve refletir a extração mais recente dos providers (ex.: UpToData), corrigindo casos como DAP ausente em uma única `data_referencia`.

## Problem statement (contexto)

### Comportamento atual de `force`

`update_database()` usa:

```text
should_sync = force or has_mandatory_gaps(gaps_before)
```

Porém:

| Camada | Incremental atual | Efeito com `force=True` |
|--------|-------------------|-------------------------|
| Bronze | `missing_partition_values` — partição existe → não reextrai | Inalterado |
| Silver | `missing_silver_partitions` — silver existe → não renormaliza (`ajustes_bmf` não compara mtime com bronze) | Inalterado |
| Gold | `missing_persisted_dates` — qualquer linha na data → data “ok” | Inalterado |

`force=True` hoje significa apenas **“rodar o pipeline mesmo sem gaps obrigatórios”**, não **“sobrescrever dados existentes”**.

### Caso real

Consumidor com `data_root` externo: primeira ingestão de `2026-05-25` grava bronze/silver/gold incompletos (só `DI1`); CSV B3 posteriormente completo; `update(force=True)` não corrige porque as partições permanecem.

## Design decision — API pública

### DD-001 — `force` permanece em `update()`, não em `read_data()`

- `read_data()` continua **read-only** (FR da `003-public-gold-reader-api`).
- Refresh destrutivo é responsabilidade de **`update()`** / pipeline.
- Documentar em README e `docs/README_PACKAGE_USER_DRAFT.md`.

### DD-002 — Semântica de `force=False` (inalterada)

`force=False` (default): comportamento incremental atual (só lacunas / gaps).

### DD-003 — Semântica nova de `force=True`

`force=True` deve executar, **antes** do sync, uma fase de **invalidação** no escopo definido e, em seguida, bronze → silver → gold como hoje.

Escopo padrão quando `force=True`:

| Parâmetro | Default com `force=True` | Efeito |
|-----------|--------------------------|--------|
| `datasets` | `None` → todos os datasets do pipeline | Quais datasets/builders invalidar |
| `start_date` / `end_date` | janela canônica de sync (`sync_start_date` … `sync_end_date`) | Quais partições diárias/mensais |
| `data_root` | via overlay (`ensure_local_environment`) ou layout dev | Só apagar sob lake/DB resolvidos |

### DD-004 — Escopo universal: todos os datasets do sistema

`force=True` deve funcionar para **cada dataset** registrado em `app.core.datasets.DATASETS` e para **cada builder** gold correspondente (`app.lake.gold.contracts.BUILDER_NAMES`, exceto `vna_lft` se ainda não implementado).

Lista canônica (v1):

| Dataset (bronze/silver) | Builder gold | Granularidade |
|-------------------------|--------------|---------------|
| `cdi` | `cdi` | dia |
| `ptax` | `ptax` | dia |
| `mercado_secundario` | `mercado_secundario` | dia |
| `liquidacoes_mercado` | `liquidacoes_mercado` | dia |
| `leiloes` | `leiloes` | dia |
| `ajustes_bmf` | `bmf` | dia |
| `ipca_indice` | `ipca_dict` | mês |
| `projecoes` | `ipca_dict` | mês |
| `feriados` | `feriados` | snapshot |

Nenhum dataset do pipeline pode ficar de fora da invalidação/reprocessamento quando estiver no escopo (`datasets=None` ou nome explícito na lista).

### DD-005 — Parâmetro opcional `refresh_dates`

Adicionar em `update()`:

```python
refresh_dates: list[str] | None = None
```

- `force=True` + `refresh_dates=["2026-05-25"]` → invalidar/reprocessar **apenas** essa(s) data(s) nos datasets/builders afetados.
- `force=True` + `refresh_dates=None` → invalidar toda a janela `start_date`…`end_date` (ou janela canônica se ambos `None`).
- Reduz custo vs apagar o lake inteiro.

**Alternativa rejeitada (v1):** `force=True` sempre apaga todo o `data_root/lake` — muito destrutivo para consumidores com histórico longo.

## Functional requirements

### FR-001 — Fase de invalidação antes do sync

Nova etapa interna (ex.: `invalidate_pipeline_scope`) chamada de `update_database()` quando `force=True`, **antes** de `run_daily_sync()`.

Para cada dataset diário no escopo:

1. Remover artefato bronze: `{bronze_root}/{dataset}/data={YYYY-MM-DD}/part.{ext}`
2. Remover artefato silver: `{silver_root}/{dataset}/data={YYYY-MM-DD}/part.parquet`
3. Para datasets mensais (`ipca_indice`, `projecoes`): remover `reference_month={YYYY-MM-01}/...` no escopo de meses derivados das datas/da janela
4. Para snapshot (`feriados`): remover `snapshot=1` quando `feriados` ∈ escopo

### FR-002 — Invalidação gold (SQLite)

Para cada builder mapeado em `BUILDER_TABLE` cujo dataset silver foi invalidado:

- Executar `DELETE FROM <table> WHERE <date_col> IN (...)` para as datas do escopo (builders diários)
- Builder `ipca_dict`: seguir **FR-009** (conjunto de dias calendário a rematerializar, não apenas “datas do refresh_dates” isoladas)
- Builders diários: `cdi`, `ptax`, `bmf`, `mercado_secundario`, `liquidacoes_mercado`, `leiloes`
- `feriados`: limpar `FERIADOS` (snapshot) quando `feriados` no escopo
- `CONTRATOS_BMF`: **não** apagar tabela inteira na v1; contratos continuam via upsert por ticker

Usar `db_path` do overlay (`data_root/database/app.db`) durante `update(data_root=...)`.

### FR-003 — Sync subsequente repopula tudo

Após invalidação, `run_daily_sync()` deve:

- Reextrair bronze (partições removidas = “missing”)
- Renormalizar silver
- Rematerializar gold e persistir via repositories

Comportamento idêntico ao incremental, mas com partições limpas no escopo.

### FR-004 — Mapeamento dataset ↔ builder

| Dataset(s) silver | Builder gold | Tabela SQL |
|-------------------|--------------|------------|
| `ajustes_bmf` | `bmf` | `AJUSTES_BMF` |
| `cdi` | `cdi` | `CDI` |
| `ptax` | `ptax` | `PTAX` |
| `mercado_secundario` | `mercado_secundario` | `MERCADO_SECUNDARIO` |
| `liquidacoes_mercado` | `liquidacoes_mercado` | `LIQUIDACOES_MERCADO` |
| `leiloes` | `leiloes` | `LEILOES` |
| `ipca_indice` + `projecoes` | `ipca_dict` | `IPCA_DICT` |
| `feriados` | `feriados` | `FERIADOS` |

Invalidar partições silver de `ipca_indice` / `projecoes` quando esses datasets estiverem no escopo (ver FR-009).

### FR-005 — `force=True` com `datasets` restrito

```python
bbdb.update(
    data_root="./data/brazilian_bonds_db",
    datasets=["ajustes_bmf"],
    start_date="2026-05-25",
    end_date="2026-05-25",
    force=True,
)
```

Deve invalidar e reprocessar **somente** `ajustes_bmf` + builder `bmf` + linhas SQL de `AJUSTES_BMF` na(s) data(s) — não apagar CDI/PTAX/etc.

### FR-006 — Segurança de paths

- Invalidação só em paths resolvidos por `get_settings()` com overlay ativo (`ensure_local_environment`) ou layout dev explícito.
- Nunca apagar fora de `bronze_root`, `silver_root`, `db_path` resolvidos.
- Logar em INFO cada partição/arquivo removido e contagem de linhas SQL deletadas.

### FR-007 — Documentação consumidor

Atualizar:

- `README.md`
- `docs/README_PACKAGE_USER_DRAFT.md`
- docstring de `app.public.update.update()`

Texto claro:

> `force=True` **apaga e reprocessa** bronze, silver e gold no escopo (datasets + datas). `force=False` mantém incremental.

### FR-008 — `read_data()` inalterado

Sem parâmetro `force` em `read_data()`. Consumidor corrige dados com `update(force=True)` e depois `read_data()`.

### FR-009 — `ipca_dict`: preservar lógica gold atual (invariante)

**Não alterar** regras de negócio em `app.lake.gold.builders.ipca_dict` (`build_for_date`, projeções, fechado M-1, etc.) nem o fluxo de materialização em `app.lake.gold.registry._build_ipca_dict`.

Quando o escopo de `force=True` invalidar **qualquer** partição mensal de `ipca_indice` e/ou `projecoes`:

1. **Invalidação:** remover bronze/silver das partições `reference_month=YYYY-MM-01` afetadas (meses derivados do escopo, alinhado a `gold/incremental._ipca_silver_months_required_for_day` / janela de sync).
2. **Gold SQL:** remover da tabela `IPCA_DICT` todas as linhas cuja `data_referencia` pertença ao conjunto de **dias calendário a rematerializar** — não apenas o dia que disparou o refresh.
3. **Rematerialização:** após bronze/silver repopulados, o sync gold de `ipca_dict` deve reconstruir a **série diária completa** desde o primeiro dia impactado pela mudança mensal **até a data mais atual do escopo de sync** (`sync_end_date` / `end_date` / último dia candidato), **dia a dia**, chamando a mesma lógica atual (`build_for_date` por `data_referencia`, com silver mensal carregado via `read_silver_range` / `_month_range_for_ipca` no orchestrator).

Em outras palavras: invalidar um mês IPCA implica **refazer todas as linhas diárias de `IPCA_DICT` dependentes desse mês até o fim da janela**, exatamente como o pipeline gold já faz quando materializa `ipca_dict` para uma lista de datas calendário — a feature 005 só **força** essa rematerialização apagando partições/SQL antigos; **não redefine** o cálculo diário.

**Proibido na v1:**

- Atualizar só um subconjunto arbitrário de dias de `IPCA_DICT` se a lógica atual exigiria recalcular a série até a data corrente do sync.
- Introduzir atalhos que pulem dias calendário no rebuild de `ipca_dict` após invalidação mensal.

### FR-010 — Cobertura de testes por tipo de dataset

Além do caso `ajustes_bmf` (motivador), a suíte deve incluir pelo menos um teste de `force=True` para:

- dataset **diário** genérico (ex.: `cdi` ou `ptax`);
- **`ipca_dict`** após invalidação de um `reference_month` (série diária rematerializada até `end_date` do sync);
- **`feriados`** (snapshot), se no escopo.

## Non-functional requirements

### NFR-001 — Idempotência

Duas chamadas seguidas `update(..., force=True)` com mesmo escopo produzem o mesmo estado (desde que providers estáveis).

### NFR-002 — Performance

Invalidação por lista de datas deve ser O(datas × datasets) em I/O de arquivos, sem varrer lake inteiro quando `refresh_dates` informado.

### NFR-003 — Testabilidade

Testes com `tmp_path` como `data_root`: criar partição bronze “ruim”, gold com só DI1, `update(force=True)`, assert DAP presente após mock do provider.

## Acceptance criteria

1. Com bronze/silver/gold pré-populados para `2026-05-25` **sem** DAP e provider mock retornando DAP+DI1, `update(force=True, datasets=["ajustes_bmf"], start_date=..., end_date=...)` faz `read_data().ajustes_bmf.fetch_on(...)` incluir DAP.
2. `force=False` não remove partições existentes (teste de regressão).
3. `force=True` + `datasets=["cdi"]` não remove partições `ajustes_bmf`.
4. `force=True` + `datasets=None` invalida/reprocessa **todos** os datasets do pipeline na janela (smoke ou teste com mocks por dataset).
5. Após invalidar um mês de `ipca_indice` ou `projecoes`, `IPCA_DICT` contém série diária recalculada até a data final do sync, com mesmas regras de `build_for_date` (sem alteração de fórmulas).
6. Logs listam invalidação executada.
7. Documentação pública atualizada (inclui que `force` é global ao pipeline, não só BMF).

## Risks and mitigations

| Risco | Mitigação |
|-------|-----------|
| Apagar histórico longo por engano | Escopo por `refresh_dates` + `start_date`/`end_date`; logs explícitos |
| `ipca_dict` com dependência mensal | Invalidar meses necessários; rematerializar série diária até data atual do sync via lógica existente (FR-009); não mudar `build_for_date` |
| Escopo percebido como “só BMF” | Documentar e testar todos os datasets (DD-004, FR-010) |
| Corrida com outro processo no mesmo `data_root` | Documentar “não compartilhar data_root entre processos concorrentes” |

## Out of scope (v1)

- `read_data(force=True)`
- Alterar regras de cálculo ou materialização de `ipca_dict` (apenas invalidar + reexecutar pipeline existente)
- Refresh automático quando bronze mtime > silver (feature futura)
- Validação de qualidade (contagem DAP/DI1) antes de considerar partição fechada
- Apagar `CONTRATOS_BMF` órfãos
- CLI flags novas além de espelhar `update()` existente (opcional em task separada)

## Target usage (após implementação)

```python
from dotenv import load_dotenv
load_dotenv()

import brazilian_bonds_db as bbdb

bbdb.update(
    data_root="./data/brazilian_bonds_db",
    datasets=["ajustes_bmf"],
    start_date="2026-05-25",
    end_date="2026-05-25",
    force=True,
    refresh_dates=["2026-05-25"],  # opcional; restringe invalidação a datas explícitas
)

data = bbdb.read_data(data_root="./data/brazilian_bonds_db")
df = data.ajustes_bmf.fetch_on("2026-05-25")
```

## Related code (referência para implementação)

| Área | Arquivo |
|------|---------|
| Update orchestration | `src/app/services/update_database_service.py` |
| API pública | `src/app/public/update.py` |
| Registry datasets | `src/app/core/datasets.py` |
| Bronze incremental | `src/app/lake/bronze/incremental.py` |
| Silver incremental | `src/app/lake/silver/incremental.py` |
| Gold gaps | `src/app/lake/gold/incremental.py` |
| IPCA dict builder (não alterar lógica) | `src/app/lake/gold/builders/ipca_dict.py`, `src/app/lake/gold/registry.py` |
| Sync | `src/app/services/sync_runner.py` |
