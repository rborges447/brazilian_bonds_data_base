# Gold read queries

Naming: `{dataset}_{mode}.sql`

| Mode | Parameters |
|------|------------|
| `*_latest` | `?` = number of **distinct reference dates** (not row count); returns all rows for those dates |
| `*_on_date` | `?` = ISO date |
| `*_range` | `?`, `?` = start, end (inclusive) |
| `*_all` | none |

Daily series use `data_referencia`; `feriados` uses `data` (SQL only; public API uses `fetch_all` on feriados).

Join: `mercado_liquidacoes_full_outer_*` — full outer mercado + liquidações by título/date.

`fetch_latest` canonical pattern:

```sql
WITH latest_dates AS (
    SELECT data_referencia FROM <TABLE>
    GROUP BY data_referencia
    ORDER BY data_referencia DESC
    LIMIT ?
)
SELECT ... FROM <TABLE> t
WHERE t.data_referencia IN (SELECT data_referencia FROM latest_dates)
ORDER BY ...;
```
