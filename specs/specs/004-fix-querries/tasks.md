# Tasks — 004 `fetch_latest` por últimas n datas

## Agent Rule

Execute **one task at a time**.

Corrigir na **raiz** (`*_latest.sql`). Não adicionar helpers Python para datas em readers, exceto o necessário para FR-003 (readers estáticos só com `fetch_all`).

**Context:** `read_data()` → `GoldReader` → SQL em `src/app/database/queries/`.

---

## Task 1 — Atualizar contrato em `queries/_README.md`

### Goal

Documentar que `*_latest` usa `?` = número de **datas distintas**, não de linhas.

### Files

- `src/app/database/queries/_README.md`

### Do not

- Alterar arquivos `.sql` nesta tarefa

---

## Task 2 — Inventariar `*_latest.sql`

### Goal

Classificar cada query: 1:1 por data, multi-linha, combined full outer, ou fora de uso (feriados/títulos/contratos na API).

### Checklist

| Arquivo | Tipo | Ação Task |
|---------|------|-----------|
| `cdi_latest.sql` | 1:1 | Task 8 |
| `ptax_latest.sql` | 1:1 | Task 8 |
| `ipca_dict_latest.sql` | 1:1 | Task 8 |
| `mercado_secundario_latest.sql` | multi-linha | Task 3 |
| `liquidacoes_mercado_latest.sql` | multi-linha | Task 4 |
| `leiloes_latest.sql` | multi-linha | Task 5 |
| `ajustes_bmf_latest.sql` | multi-linha | Task 6 |
| `mercado_liquidacoes_full_outer_latest.sql` | combined | Task 7 |
| `feriados_latest.sql` | API: não usar | — |
| `titulos_publicos_latest.sql` | API: não usar | Task 10 |
| `contratos_bmf_latest.sql` | API: não usar | Task 10 |

### Do not

- Implementar SQL ainda

---

## Task 3 — `mercado_secundario_latest.sql`

### Goal

CTE `latest_dates` + `WHERE data_referencia IN (...)`.

### Files

- `src/app/database/queries/mercado_secundario_latest.sql`
- Teste em Task 9

### Do not

- Alterar `_on_date` / `_range`

---

## Task 4 — `liquidacoes_mercado_latest.sql`

### Goal

Mesmo padrão CTE que Task 3.

### Files

- `src/app/database/queries/liquidacoes_mercado_latest.sql`

---

## Task 5 — `leiloes_latest.sql`

### Goal

Mesmo padrão CTE; manter `ORDER BY` com `numero_edital`, `tipo_titulo`, `data_vencimento`.

### Files

- `src/app/database/queries/leiloes_latest.sql`

---

## Task 6 — `ajustes_bmf_latest.sql`

### Goal

Mesmo padrão CTE; manter desempate por `ticker`.

### Files

- `src/app/database/queries/ajustes_bmf_latest.sql`

---

## Task 7 — `mercado_liquidacoes_full_outer_latest.sql`

### Goal

CTE com `UNION` de datas de `MERCADO_SECUNDARIO` e `LIQUIDACOES_MERCADO`; filtrar subquery full outer; remover `LIMIT` final sobre linhas.

### Files

- `src/app/database/queries/mercado_liquidacoes_full_outer_latest.sql`
- Estender `tests/database/test_gold_reader.py` (cenário `fetch_latest`)

### Do not

- Alterar `_on_date` / `_range` / `_all` do full outer

---

## Task 8 — Alinhar `cdi`, `ptax`, `ipca_dict`

### Goal

Reescrever `*_latest.sql` com CTE canônico; regressão em `test_cdi_date_series_readers`.

### Files

- `src/app/database/queries/cdi_latest.sql`
- `src/app/database/queries/ptax_latest.sql`
- `src/app/database/queries/ipca_dict_latest.sql`

---

## Task 9 — Testes `fetch_latest` por datas distintas

### Goal

Testes com seed multi-linha provando `n` datas distintas e contagem de linhas correta.

### Files

- `tests/database/test_fetch_latest_dates.py` (novo) ou ampliar `tests/database/test_gold_reader.py`

### Casos mínimos

- `mercado_secundario.fetch_latest(2)` → 2 datas, todas as linhas de cada data
- `leiloes` ou `liquidacoes_mercado` (pelo menos um)
- `mercado_com_liquidacoes.fetch_latest(2)` com datas só em mercado / só em liq / em ambos

---

## Task 10 — Readers: só `fetch_all` para feriados, titulos, contratos

### Goal

- `FeriadosReader` (ou estático em `_static.py`): apenas `fetch_all()`
- `TitulosPublicosReader`, `ContratosBmfReader`: remover `fetch_latest`; `fetch_on` / `fetch_range` → `TypeError` citando `fetch_all()`
- Atualizar `gold_reader.py` docstring

### Files

- `src/app/database/readers/_static.py`
- `src/app/database/readers/gold_reader.py`

### Do not

- Expor `DateSeriesTableReader` para `feriados`

---

## Task 11 — Documentação pública

### Goal

Atualizar contrato de `fetch_latest` para “últimas n datas”; tabelas dimensão/feriados só `fetch_all`.

### Files

- `docs/gold_reader_public_api.md`
- `README.md` (seção `read_data`)

### Do not

- Inventar datasets ou métodos inexistentes

---

## Task 12 — Verificação final

### Goal

```bash
pytest tests/database tests/public -q
```

Ajustar qualquer teste que chamava `feriados.fetch_latest`, `titulos_publicos.fetch_latest`, etc.

### Do not

- Alterar lake/CLI nesta tarefa
