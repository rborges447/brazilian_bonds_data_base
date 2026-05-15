"""Product read queries against the database."""

from rf_lake.gold.db.queries.ajustes_bmf import get_ajustes_bmf
from rf_lake.gold.db.queries.common import apply_date_filters
from rf_lake.gold.db.queries.contratos_bmf import get_contratos_bmf
from rf_lake.gold.db.queries.datas import (
    get_max_date,
    list_dates,
    missing_dates_for_table,
)
from rf_lake.gold.db.queries.feriados import get_feriados
from rf_lake.gold.db.queries.ipca_indice import (
    get_ipca_indice,
    get_ipca_indice_last_months,
)
from rf_lake.gold.db.queries.job_runs import get_job_runs
from rf_lake.gold.db.queries.leiloes import get_leiloes
from rf_lake.gold.db.queries.liquidacoes_mercado import get_liquidacoes_mercado
from rf_lake.gold.db.queries.mercado_secundario import get_mercado_secundario
from rf_lake.gold.db.queries.mercado_secundario_liquidacoes import (
    get_mercado_secundario_com_liquidacoes,
)
from rf_lake.gold.db.queries.projecoes import get_projecoes
from rf_lake.gold.db.queries.schema_migrations import get_schema_migrations
from rf_lake.gold.db.queries.titulos_publicos import get_titulos_publicos

__all__ = [
    "apply_date_filters",
    "get_ajustes_bmf",
    "get_contratos_bmf",
    "get_feriados",
    "get_ipca_indice",
    "get_ipca_indice_last_months",
    "get_job_runs",
    "get_leiloes",
    "get_liquidacoes_mercado",
    "get_max_date",
    "get_mercado_secundario",
    "get_mercado_secundario_com_liquidacoes",
    "get_projecoes",
    "get_schema_migrations",
    "get_titulos_publicos",
    "list_dates",
    "missing_dates_for_table",
]
