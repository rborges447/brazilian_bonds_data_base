# Gold read queries

Naming: `{dataset}_{mode}.sql`

| Mode | Parameters |
|------|------------|
| `*_latest` | `?` = LIMIT n |
| `*_on_date` | `?` = ISO date |
| `*_range` | `?`, `?` = start, end (inclusive) |
| `*_all` | none |

Daily series use `data_referencia`; `feriados` uses `data`.

Join: `mercado_liquidacoes_full_outer_*` — full outer mercado + liquidações by título/date.
