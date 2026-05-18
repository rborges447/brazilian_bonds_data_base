"""
Data platform reader.

Main facade for external consumers (calculator, analytics, Dash/API).
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Optional, Tuple

import pandas as pd

from rf_lake.gold.db import get_conn
from rf_lake.gold.db.queries import (
    apply_date_filters as _apply_date_filters,
    get_ajustes_bmf as _q_get_ajustes_bmf,
    get_contratos_bmf as _q_get_contratos_bmf,
    get_feriados as _q_get_feriados,
    get_ipca_indice as _q_get_ipca_indice,
    get_ipca_indice_last_months as _q_get_ipca_indice_last_months,
    get_job_runs as _q_get_job_runs,
    get_leiloes as _q_get_leiloes,
    get_liquidacoes_mercado as _q_get_liquidacoes_mercado,
    get_max_date as _get_max_date,
    get_mercado_secundario as _q_get_mercado_secundario,
    get_mercado_secundario_com_liquidacoes as _q_get_mercado_secundario_com_liquidacoes,
    get_projecoes as _q_get_projecoes,
    get_schema_migrations as _q_get_schema_migrations,
    get_titulos_publicos as _q_get_titulos_publicos,
    missing_dates_for_table as _missing_dates_for_table,
)
from rf_lake.gold.db.repositories import ContratosBmfRepo, TitulosPublicosRepo
from rf_lake.jobs import backfill, run_daily, run_one
from rf_lake.settings import DB_PATH


class Database:
    """
    Public interface for SQLite database operations.

    Centralizes database access for other modules.

    Thread-safe: each operation opens its own connection.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize Database.

        Args:
            db_path: Optional path to the database file.
                     If omitted, uses the configured default path.
        """
        self._db_path = db_path or DB_PATH
    
    @contextmanager
    def _get_connection(self):
        """
        Context manager yielding a database connection.

        Ensures the connection is closed after use.
        """
        conn = get_conn(self._db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    # ============================================================================
    # READ QUERIES (PUBLIC API)
    # ============================================================================

    @staticmethod
    def _apply_date_filters(
        sql: str,
        params: list,
        *,
        date_col: str,
        ref_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> tuple[str, list]:
        """
        Apply date filters (ISO YYYY-MM-DD) to SQL.

        Rules:
        - if `ref_date` is set, `start_date`/`end_date` must not be used
        - `start_date` and/or `end_date` define an inclusive range
        - if none are set, no date filter is applied
        """
        return _apply_date_filters(
            sql,
            params,
            date_col=date_col,
            ref_date=ref_date,
            start_date=start_date,
            end_date=end_date,
        )
    
    def get_mercado_secundario(
        self,
        ref_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        tipo_titulo: Optional[str] = None,
        data_vencimento: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Query secondary market data.

        Args:
            ref_date: Exact reference date 'YYYY-MM-DD'
            start_date: Start date (inclusive) 'YYYY-MM-DD'
            end_date: End date (inclusive) 'YYYY-MM-DD'
            tipo_titulo: Optional filter by bond type
            data_vencimento: Optional filter by maturity (YYYY-MM-DD)

        Returns:
            DataFrame of secondary market rows
        """
        with self._get_connection() as conn:
            return _q_get_mercado_secundario(
                conn,
                ref_date=ref_date,
                start_date=start_date,
                end_date=end_date,
                tipo_titulo=tipo_titulo,
                data_vencimento=data_vencimento,
            )
    
    def get_liquidacoes_mercado(
        self,
        ref_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        tipo_titulo: Optional[str] = None,
        data_vencimento: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Query market settlement data.

        Args:
            ref_date: Exact reference date 'YYYY-MM-DD'
            start_date: Start date (inclusive) 'YYYY-MM-DD'
            end_date: End date (inclusive) 'YYYY-MM-DD'
            tipo_titulo: Optional filter by bond type
            data_vencimento: Optional filter by maturity (YYYY-MM-DD)

        Returns:
            DataFrame of settlement rows
        """
        with self._get_connection() as conn:
            return _q_get_liquidacoes_mercado(
                conn,
                ref_date=ref_date,
                start_date=start_date,
                end_date=end_date,
                tipo_titulo=tipo_titulo,
                data_vencimento=data_vencimento,
            )

    def get_mercado_secundario_com_liquidacoes(
        self,
        ref_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        tipo_titulo: Optional[str] = None,
        data_vencimento: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Query secondary market and settlements in one DataFrame (taxa_anbima and qtd_titulos).
        """
        with self._get_connection() as conn:
            return _q_get_mercado_secundario_com_liquidacoes(
                conn,
                ref_date=ref_date,
                start_date=start_date,
                end_date=end_date,
                tipo_titulo=tipo_titulo,
                data_vencimento=data_vencimento,
            )

    def get_ajustes_bmf(
        self,
        ref_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        ticker: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Query BMF adjustment rows.

        Args:
            ref_date: Exact reference date 'YYYY-MM-DD'
            start_date: Start date (inclusive) 'YYYY-MM-DD'
            end_date: End date (inclusive) 'YYYY-MM-DD'
            ticker: Optional ticker filter

        Returns:
            DataFrame of BMF adjustment rows
        """
        with self._get_connection() as conn:
            return _q_get_ajustes_bmf(
                conn,
                ref_date=ref_date,
                start_date=start_date,
                end_date=end_date,
                ticker=ticker,
            )
    
    def get_titulos_publicos(
        self,
        tipo_titulo: Optional[str] = None,
        data_vencimento: Optional[str] = None,
        status: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Query government bonds (master/reference data).

        Returns:
            DataFrame of all matching bonds
        """
        with self._get_connection() as conn:
            return _q_get_titulos_publicos(
                conn,
                tipo_titulo=tipo_titulo,
                data_vencimento=data_vencimento,
                status=status,
            )

    def list_ativos(self) -> pd.DataFrame:
        """
        Alias for `get_titulos_publicos()` (backward compatibility).
        """
        return self.get_titulos_publicos()

    def get_contratos_bmf(self, ticker: Optional[str] = None) -> pd.DataFrame:
        """
        Query BMF contracts (master/reference data).
        """
        with self._get_connection() as conn:
            return _q_get_contratos_bmf(conn, ticker=ticker)
    
    def get_leiloes(
        self,
        data_referencia: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        tipo_titulo: Optional[str] = None,
        data_vencimento: Optional[str] = None,
        numero_edital: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Query auction data (results + offering) from LEILOES.

        Args:
            data_referencia: Exact date 'YYYY-MM-DD'
            start_date: Start date (inclusive) 'YYYY-MM-DD'
            end_date: End date (inclusive) 'YYYY-MM-DD'
            tipo_titulo: Optional filter by bond type
            data_vencimento: Optional filter by maturity
            numero_edital: Optional filter by notice number

        Returns:
            DataFrame of auction rows
        """
        with self._get_connection() as conn:
            return _q_get_leiloes(
                conn,
                data_referencia=data_referencia,
                start_date=start_date,
                end_date=end_date,
                tipo_titulo=tipo_titulo,
                data_vencimento=data_vencimento,
                numero_edital=numero_edital,
            )

    def get_ipca_indice(
        self,
        ref_month: Optional[str] = None,
        start_month: Optional[str] = None,
        end_month: Optional[str] = None,
        start_year: Optional[int] = None,
        start_month_num: Optional[int] = None,
        end_year: Optional[int] = None,
        end_month_num: Optional[int] = None,
        last: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Query monthly IPCA (IPCA_INDICE table).

        Modes: last=N (last N months); start_year/start_month_num/end_year/end_month_num (range);
        ref_month or start_month/end_month in ISO (legacy); or no filter (all rows).
        Dates in ISO YYYY-MM-DD, always day 01.
        """
        with self._get_connection() as conn:
            return _q_get_ipca_indice(
                conn,
                ref_month=ref_month,
                start_month=start_month,
                end_month=end_month,
                start_year=start_year,
                start_month_num=start_month_num,
                end_year=end_year,
                end_month_num=end_month_num,
                last=last,
            )

    def get_ipca_indice_last_months(self, months: int) -> pd.DataFrame:
        """
        Return the last `months` IPCA_INDICE rows (ascending by ref_month).
        """
        with self._get_connection() as conn:
            return _q_get_ipca_indice_last_months(conn, months=int(months))

    def get_projecoes(
        self,
        indice: Optional[str] = None,
        ref_month: Optional[str] = None,
        start_data_coleta: Optional[str] = None,
        end_data_coleta: Optional[str] = None,
        start_year: Optional[int] = None,
        start_month: Optional[int] = None,
        end_year: Optional[int] = None,
        end_month: Optional[int] = None,
        last: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Query projections (PROJECOES table).

        ref_month modes: last=N; start_year/start_month/end_year/end_month (range);
        exact ref_month (MM/YYYY); or all rows. data_coleta in ISO YYYY-MM-DD.
        """
        with self._get_connection() as conn:
            return _q_get_projecoes(
                conn,
                indice=indice,
                ref_month=ref_month,
                start_data_coleta=start_data_coleta,
                end_data_coleta=end_data_coleta,
                start_year=start_year,
                start_month=start_month,
                end_year=end_year,
                end_month=end_month,
                last=last,
            )

    def get_feriados(self) -> pd.DataFrame:
        """
        Query national holidays (FERIADOS table).
        Column `data` as str "YYYY-MM-DD".
        """
        with self._get_connection() as conn:
            return _q_get_feriados(conn)

    def get_job_runs(
        self,
        pipeline_name: Optional[str] = None,
        ref_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Query the `job_runs` table.
        """
        with self._get_connection() as conn:
            return _q_get_job_runs(
                conn,
                pipeline_name=pipeline_name,
                ref_date=ref_date,
                start_date=start_date,
                end_date=end_date,
                status=status,
            )

    def get_schema_migrations(self) -> pd.DataFrame:
        """
        Query the `schema_migrations` table.
        """
        with self._get_connection() as conn:
            return _q_get_schema_migrations(conn)
    
    # ============================================================================
    # JOBS (PUBLIC API)
    # ============================================================================
    
    def run_daily(self, date: Optional[str] = None) -> dict:
        """
        Run the end-to-end daily job (all pipelines).

        Args:
            date: Date 'YYYY-MM-DD' (None = today)

        Returns:
            dict with per-pipeline results
        """
        return run_daily(date)
    
    def backfill(
        self,
        start_date: str,
        end_date: str,
        pipeline: Optional[str] = None,
    ) -> dict:
        """
        Run backfill over a date range.

        Args:
            start_date: Start 'YYYY-MM-DD'
            end_date: End 'YYYY-MM-DD'
            pipeline: Pipeline name (None = all)

        Returns:
            dict with results
        """
        return backfill(start_date, end_date, pipeline)
    
    def run_one(self, pipeline: str, date: str) -> dict:
        """
        Run a single pipeline for one date (debug).

        Args:
            pipeline: Pipeline name
            date: Date 'YYYY-MM-DD'

        Returns:
            dict with pipeline result
        """
        return run_one(pipeline, date)
    
    # ============================================================================
    # GOVERNMENT BOND OPERATIONS
    # ============================================================================
    
    def get_titulo_publico_id(
        self,
        tipo_titulo: str,
        data_vencimento: str,
    ) -> Optional[Tuple[str, str]]:
        """
        Look up the primary key for a government bond.

        Args:
            tipo_titulo: Bond type (e.g. 'NTN-B', 'LFT', 'LTN')
            data_vencimento: Maturity 'YYYY-MM-DD'

        Returns:
            (tipo_titulo, data_vencimento) if found, else None.
        """
        with self._get_connection() as conn:
            row = TitulosPublicosRepo.get_by_pk(conn, tipo_titulo, data_vencimento)
            if row is None:
                return None
            return (tipo_titulo, data_vencimento)
    
    def get_or_create_titulo_publico(
        self,
        tipo_titulo: str,
        data_vencimento: str,
        expressao: Optional[str] = None,
        data_base: Optional[str] = None,
        codigo_selic: Optional[str] = None,
        codigo_isin: Optional[str] = None,
        status: str = "ATIVO",
    ) -> Tuple[str, str]:
        """
        Get or create a government bond row.

        Args:
            tipo_titulo: Bond type (e.g. 'NTN-B', 'LFT', 'LTN')
            data_vencimento: Maturity 'YYYY-MM-DD'
            expressao: Bond expression (optional)
            data_base: Base date (optional)
            codigo_selic: SELIC code (optional)
            codigo_isin: ISIN (optional)
            status: Status (default: 'ATIVO')

        Returns:
            Primary key (tipo_titulo, data_vencimento).
        """
        with self._get_connection() as conn:
            titulo_id = TitulosPublicosRepo.get_or_create(
                conn=conn,
                tipo_titulo=tipo_titulo,
                data_vencimento=data_vencimento,
                expressao=expressao,
                data_base=data_base,
                codigo_selic=codigo_selic,
                codigo_isin=codigo_isin,
                status=status,
            )
            conn.commit()
            return titulo_id
    
    # ============================================================================
    # BMF CONTRACT OPERATIONS
    # ============================================================================
    
    def contrato_bmf_exists(self, ticker: str) -> bool:
        """
        Return whether a BMF contract exists.

        Args:
            ticker: Contract ticker (e.g. 'DI1F26')

        Returns:
            True if it exists, False otherwise.
        """
        with self._get_connection() as conn:
            return ContratosBmfRepo.exists(conn, ticker)
    
    def get_or_create_contrato_bmf(
        self,
        ticker: str,
        codigo_isin: Optional[str] = None,
        data_vencimento: Optional[str] = None,
    ) -> str:
        """
        Get or create a BMF contract.

        Args:
            ticker: Contract ticker (e.g. 'DI1F26')
            codigo_isin: ISIN (optional)
            data_vencimento: Maturity 'YYYY-MM-DD' (optional)

        Returns:
            The contract ticker (same as input).
        """
        with self._get_connection() as conn:
            ticker_result = ContratosBmfRepo.get_or_create(
                conn=conn,
                ticker=ticker,
                codigo_isin=codigo_isin,
                data_vencimento=data_vencimento,
            )
            conn.commit()
            return ticker_result
    
    # ============================================================================
    # DATE QUERIES
    # ============================================================================
    
    def get_max_date(self, table: str, date_col: str) -> Optional[str]:
        """
        Maximum date value in `date_col` for `table`.

        Args:
            table: Table name
            date_col: Date column name

        Returns:
            Max date 'YYYY-MM-DD', or None if the table is empty.
        """
        return _get_max_date(table, date_col)
    
    def missing_dates_for_table(
        self,
        table: str,
        date_col: str,
        default_start: str = "2018-01-01",
        end_date: Optional[str] = None,
        skip_weekends: bool = True,
    ) -> list[str]:
        """
        List missing dates for a table.

        Rule:
        - If the table has dates: start the day after MAX(date_col)
        - Otherwise: start at default_start

        Args:
            table: Table name
            date_col: Date column name
            default_start: Default start if the table is empty
            end_date: End date (default: yesterday)
            skip_weekends: If True, skip weekends

        Returns:
            List of dates 'YYYY-MM-DD'.
        """
        return _missing_dates_for_table(
            table=table,
            date_col=date_col,
            default_start=default_start,
            end_date=end_date,
            skip_weekends=skip_weekends,
        )

    def get_last_source_date(
        self,
        dataset: str,
        layer: str = "bronze",
    ) -> Optional[str]:
        """
        Last business date with a non-empty artifact in raw/silver.

        Unlike get_max_date (Gold/SQLite): reflects what extraction has produced.
        """
        from rf_lake.watermarks import get_watermark

        return get_watermark(dataset, layer)

    def get_freshness_summary(self) -> "pd.DataFrame":
        """
        Per-dataset summary: last bronze/silver dates and Gold MAX in SQLite.
        """
        import pandas as pd

        from rf_lake.datasets import DATASETS
        from rf_lake.watermarks import get_all_watermarks

        wm = get_all_watermarks()
        rows: list[dict] = []
        for name, cfg in DATASETS.items():
            gold_max = None
            if cfg.table and cfg.date_col:
                gold_max = self.get_max_date(cfg.table, cfg.date_col)
            entry = wm.get(name, {})
            rows.append(
                {
                    "dataset": name,
                    "bronze_last_date": entry.get("bronze"),
                    "silver_last_date": entry.get("silver"),
                    "gold_max_date": gold_max,
                }
            )
        return pd.DataFrame(rows)
    
    # ============================================================================
    # DIRECT REPOSITORY ACCESS (advanced)
    # ============================================================================
    
    @contextmanager
    def transaction(self):
        """
        Context manager that runs operations in a transaction.

        Use when multiple steps must commit atomically.

        Example:
            with db.transaction() as conn:
                # Multiple operations using conn directly
                TitulosPublicosRepo.get_or_create(conn, ...)
                LiquidacoesMercadoRepo.upsert(conn, ...)
                # Commits automatically on successful exit
        """
        conn = get_conn(self._db_path)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def execute_query(self, sql: str, params: tuple = ()) -> list[tuple]:
        """
        Run a SQL query and return all rows.

        WARNING: Prefer higher-level methods when possible.

        Args:
            sql: SQL statement
            params: Query parameters (tuple)

        Returns:
            List of result tuples.
        """
        with self._get_connection() as conn:
            return conn.execute(sql, params).fetchall()
    
    def execute_update(self, sql: str, params: tuple = ()) -> int:
        """
        Run a SQL update (INSERT, UPDATE, DELETE).

        WARNING: Prefer higher-level methods when possible.

        Args:
            sql: SQL statement
            params: Query parameters (tuple)

        Returns:
            Number of affected rows.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor.rowcount
