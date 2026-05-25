# Feature Spec — `fetch_latest` por últimas n datas disponíveis

## Feature Name

`004-fix-querries`

## Status and dependencies

- **Prerequisites (completed):** `001-public-database-api`, `002-import-alias-brazilian-bonds-db`, `003-public-gold-reader-api`
- **Scope:** corrigir queries `*_latest.sql` e contrato de `fetch_latest(n)`; simplificar API de `feriados`, `titulos_publicos`, `contratos_bmf`
- **Out of scope:** lake/bronze/silver, `update()`, migrations de schema, legacy `rf_lake/`

## Objective

Garantir que, para qualquer dataset com coluna de data exposto em `read_data()` / `GoldReader`, o método `fetch_latest(n)` retorne **todas as linhas** das **últimas n datas distintas** disponíveis na tabela — e não as últimas n linhas físicas do `ORDER BY ... LIMIT n`.

A correção deve ocorrer **na raiz** (`src/app/database/queries/*_latest.sql`), sem abstrações ou pós-processamento em Python nos readers.

## Current context

### Fluxo de leitura

```text
bbdb.read_data()  →  GoldReader  →  DateSeriesTableReader / MercadoLiquidacoesReader
                                      →  load_query("{prefix}_latest")
                                      →  query_to_dataframe(sql, (n,))
```

Implementação dos readers: `src/app/database/readers/_date_series.py` (apenas delega ao SQL).

Queries: `src/app/database/queries/`.

### Por que CDI e PTAX “funcionam” hoje

Tabelas com **uma linha por `data_referencia`** (`CDI`, `PTAX`, `IPCA_DICT`). Nesses casos, `ORDER BY data_referencia DESC LIMIT n` coincide com “últimas n datas”.

### Por que mercado_secundario e leilões falham

Tabelas com **várias linhas por `data_referencia`** (por título, vencimento, edital, ticker, etc.). O `LIMIT n` atual corta **linhas**, não **datas**.

Exemplo: 3 datas × 50 títulos → `fetch_latest(5)` devolve 5 linhas (possivelmente de uma única data), em vez de todas as linhas das 5 datas mais recentes.

Afeta (entre outros):

- `mercado_secundario_latest.sql`
- `liquidacoes_mercado_latest.sql`
- `leiloes_latest.sql`
- `ajustes_bmf_latest.sql`
- `mercado_liquidacoes_full_outer_latest.sql`

`fetch_on(date)` e `fetch_range(start, end)` já filtram por data corretamente; **não** entram nesta feature.

## Functional requirements

### FR-001 — Contrato `fetch_latest(n)` em séries por data

Para datasets **date-partitioned** em `GoldReader`:

| Método | Semântica |
|--------|-----------|
| `fetch_latest(n)` | `n >= 1`; retorna **todas** as linhas cuja `data_referencia` pertence ao conjunto das **n datas distintas mais recentes** (ordenadas DESC) |
| `fetch_on(date)` | Inalterado: todas as linhas da data informada |
| `fetch_range(start, end)` | Inalterado |
| `fetch_all()` | Inalterado |

**Invariante (exemplo de teste):**

- Seed: datas `D1 < D2 < D3`, 2 títulos por data → 6 linhas no total.
- `fetch_latest(2)` → 4 linhas; `data_referencia` ∈ `{D2, D3}` apenas.

**Nota para consumidores:** `len(fetch_latest(n))` pode ser muito maior que `n` em tabelas multi-linha; `n` conta **datas**, não linhas.

### FR-002 — Correção apenas nas queries SQL

Reescrever `src/app/database/queries/*_latest.sql` afetados usando padrão canônico com CTE:

```sql
WITH latest_dates AS (
    SELECT data_referencia
    FROM <TABELA>
    GROUP BY data_referencia
    ORDER BY data_referencia DESC
    LIMIT ?
)
SELECT <colunas>
FROM <TABELA> t
WHERE t.data_referencia IN (SELECT data_referencia FROM latest_dates)
ORDER BY t.data_referencia DESC, <desempates existentes>;
```

Para `mercado_liquidacoes_full_outer_latest.sql`, a CTE de datas usa **UNION** das datas distintas de `MERCADO_SECUNDARIO` e `LIQUIDACOES_MERCADO`, depois filtra o resultado do full outer.

Tabelas 1:1 (`cdi`, `ptax`, `ipca_dict`) devem usar o mesmo padrão para **uniformidade** (comportamento observável inalterado).

**Proibido nesta feature:**

- Helper Python compartilhado para “últimas n datas”
- Pós-processar `DataFrame` no reader para corrigir `LIMIT` errado

### FR-003 — `feriados`, `titulos_publicos`, `contratos_bmf`: apenas `fetch_all()`

Esses três datasets **não** possuem semântica de “últimas n datas de mercado”. Na API pública:

- Expor somente `fetch_all()`
- `fetch_latest`, `fetch_on`, `fetch_range` devem levantar `TypeError` com mensagem que indica usar `fetch_all()`

`feriados` deixa de usar `DateSeriesTableReader`; passa a reader estático equivalente a dimensão.

Arquivos SQL `feriados_latest/on_date/range` podem permanecer no repositório (não usados pela API pública) ou ser removidos em tarefa opcional.

## Datasets impactados

| Atributo `GoldReader` | Ação |
|----------------------|------|
| `cdi`, `ptax`, `ipca_dict` | Alinhar SQL ao padrão CTE (regressão) |
| `mercado_secundario`, `liquidacoes_mercado`, `leiloes`, `ajustes_bmf` | Corrigir `*_latest.sql` + testes |
| `mercado_com_liquidacoes` / `mercado_liquidacoes` | Corrigir `mercado_liquidacoes_full_outer_latest.sql` + testes |
| `feriados`, `titulos_publicos`, `contratos_bmf` | Apenas `fetch_all()` |

## Acceptance criteria

1. `pytest tests/database tests/public` passa.
2. Multi-linha: `fetch_latest(n)` retorna exatamente `n` valores distintos em `data_referencia` quando o banco tem ≥ `n` datas.
3. `cdi` / `ptax`: testes existentes de `fetch_latest` continuam válidos.
4. `feriados`, `titulos_publicos`, `contratos_bmf`: só `fetch_all()`; demais métodos → `TypeError`.
5. `docs/gold_reader_public_api.md` e README descrevem “últimas n **datas**”, não “últimas n linhas”.
6. `src/app/database/queries/_README.md` documenta `?` em `*_latest` como número de **datas** distintas.

## Breaking change (intencional)

Consumidores que interpretavam `fetch_latest(5)` em `mercado_secundario` como “5 linhas” passam a receber “5 dias completos de mercado”. Isso é **correção de bug de contrato**, não regressão de produto.

## Reference

- Implementação: `specs/specs/004-fix-querries/tasks.md`
- API pública: `docs/gold_reader_public_api.md`
- Queries: `src/app/database/queries/`
