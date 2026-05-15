"""
Leitor de dados do data platform.

Fachada principal para consumidores externos (calculadora, analytics, Dash/API).
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
    Interface pública para operações no banco de dados SQLite.
    
    Esta classe centraliza todas as operações de banco de dados e deve ser
    usada por outros módulos para acessar o banco de dados.
    
    Thread-safe: Cada operação cria sua própria conexão.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Inicializa a instância do Database.
        
        Args:
            db_path: Caminho opcional para o arquivo do banco de dados.
                     Se não fornecido, usa o caminho padrão configurado.
        """
        self._db_path = db_path or DB_PATH
    
    @contextmanager
    def _get_connection(self):
        """
        Context manager para obter uma conexão com o banco.
        
        Garante que a conexão seja fechada automaticamente após o uso.
        """
        conn = get_conn(self._db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    # ============================================================================
    # CONSULTAS (API PÚBLICA)
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
        Aplica filtros de data (ISO YYYY-MM-DD) a um SQL.

        Regras:
        - se `ref_date` for fornecido, não pode haver `start_date`/`end_date`
        - `start_date` e/ou `end_date` definem um intervalo inclusivo
        - se nenhum for fornecido, não aplica filtro por data
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
        Consulta dados de mercado secundário.
        
        Args:
            ref_date: Data de referência exata no formato 'YYYY-MM-DD'
            start_date: Data inicial (inclusive) no formato 'YYYY-MM-DD'
            end_date: Data final (inclusive) no formato 'YYYY-MM-DD'
            tipo_titulo: Filtro opcional por tipo de título
            data_vencimento: Filtro opcional por vencimento do título (YYYY-MM-DD)
            
        Returns:
            DataFrame com dados de mercado secundário
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
        Consulta dados de liquidações de mercado.
        
        Args:
            ref_date: Data de referência exata no formato 'YYYY-MM-DD'
            start_date: Data inicial (inclusive) no formato 'YYYY-MM-DD'
            end_date: Data final (inclusive) no formato 'YYYY-MM-DD'
            tipo_titulo: Filtro opcional por tipo de título
            data_vencimento: Filtro opcional por vencimento do título (YYYY-MM-DD)
            
        Returns:
            DataFrame com dados de liquidações de mercado
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
        Consulta mercado secundário e liquidações no mesmo DataFrame (taxa_anbima e qtd_titulos).
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
        Consulta dados de ajustes BMF.
        
        Args:
            ref_date: Data de referência exata no formato 'YYYY-MM-DD'
            start_date: Data inicial (inclusive) no formato 'YYYY-MM-DD'
            end_date: Data final (inclusive) no formato 'YYYY-MM-DD'
            ticker: Filtro opcional por ticker
            
        Returns:
            DataFrame com dados de ajustes BMF
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
        Consulta títulos públicos (cadastro).
        
        Returns:
            DataFrame com todos os títulos públicos
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
        Alias para `get_titulos_publicos()` (compatibilidade).
        """
        return self.get_titulos_publicos()

    def get_contratos_bmf(self, ticker: Optional[str] = None) -> pd.DataFrame:
        """
        Consulta contratos BMF (cadastro).
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
        Consulta dados de leilões (resultados + oferta) a partir da tabela LEILOES.
        
        Args:
            data_referencia: Data exata no formato 'YYYY-MM-DD'
            start_date: Data inicial (inclusive) no formato 'YYYY-MM-DD'
            end_date: Data final (inclusive) no formato 'YYYY-MM-DD'
            tipo_titulo: Filtro opcional por tipo do título
            data_vencimento: Filtro opcional por vencimento do título
            numero_edital: Filtro opcional por número do edital
            
        Returns:
            DataFrame com dados de leilões
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
        Consulta IPCA mensal (tabela IPCA_INDICE).

        Modos: last=N (últimos N meses); start_year/start_month_num/end_year/end_month_num (range);
        ref_month ou start_month/end_month em ISO (legado); ou sem filtro (tudo).
        Datas em ISO YYYY-MM-DD, sempre dia 01.
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
        Retorna os últimos `months` registros de IPCA_INDICE (ordem ascendente por ref_month).
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
        Consulta projeções (tabela PROJECOES).

        Modos para ref_month: last=N; start_year/start_month/end_year/end_month (range);
        ref_month exato (MM/YYYY); ou tudo. data_coleta em ISO YYYY-MM-DD.
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
        Consulta feriados nacionais (tabela FERIADOS).
        Coluna `data` em str "YYYY-MM-DD".
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
        Consulta a tabela `job_runs`.
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
        Consulta a tabela `schema_migrations`.
        """
        with self._get_connection() as conn:
            return _q_get_schema_migrations(conn)
    
    # ============================================================================
    # JOBS (API PÚBLICA)
    # ============================================================================
    
    def run_daily(self, date: Optional[str] = None) -> dict:
        """
        Executa job diário end-to-end (todos os pipelines).
        
        Args:
            date: Data no formato 'YYYY-MM-DD' (None = hoje)
            
        Returns:
            dict com resultados de cada pipeline
        """
        return run_daily(date)
    
    def backfill(
        self,
        start_date: str,
        end_date: str,
        pipeline: Optional[str] = None,
    ) -> dict:
        """
        Executa backfill para um intervalo de datas.
        
        Args:
            start_date: Data inicial no formato 'YYYY-MM-DD'
            end_date: Data final no formato 'YYYY-MM-DD'
            pipeline: Nome do pipeline (None = todos)
            
        Returns:
            dict com resultados
        """
        return backfill(start_date, end_date, pipeline)
    
    def run_one(self, pipeline: str, date: str) -> dict:
        """
        Executa um único pipeline para uma data específica (debug).
        
        Args:
            pipeline: Nome do pipeline
            date: Data no formato 'YYYY-MM-DD'
            
        Returns:
            dict com resultado do pipeline
        """
        return run_one(pipeline, date)
    
    # ============================================================================
    # OPERAÇÕES COM TÍTULOS PÚBLICOS
    # ============================================================================
    
    def get_titulo_publico_id(
        self,
        tipo_titulo: str,
        data_vencimento: str,
    ) -> Optional[Tuple[str, str]]:
        """
        Busca a PK de um título público.
        
        Args:
            tipo_titulo: Tipo do título (ex: 'NTN-B', 'LFT', 'LTN')
            data_vencimento: Data de vencimento no formato 'YYYY-MM-DD'
            
        Returns:
            (tipo_titulo, data_vencimento) se encontrado, None caso contrário.
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
        Busca ou cria um título público.
        
        Args:
            tipo_titulo: Tipo do título (ex: 'NTN-B', 'LFT', 'LTN')
            data_vencimento: Data de vencimento no formato 'YYYY-MM-DD'
            expressao: Expressão do título (opcional)
            data_base: Data base do título (opcional)
            codigo_selic: Código SELIC (opcional)
            codigo_isin: Código ISIN (opcional)
            status: Status do título (default: 'ATIVO')
            
        Returns:
            PK do título (tipo_titulo, data_vencimento).
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
    # OPERAÇÕES COM CONTRATOS BMF
    # ============================================================================
    
    def contrato_bmf_exists(self, ticker: str) -> bool:
        """
        Verifica se um contrato BMF existe.
        
        Args:
            ticker: Ticker do contrato (ex: 'DI1F26')
            
        Returns:
            True se existe, False caso contrário.
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
        Busca ou cria um contrato BMF.
        
        Args:
            ticker: Ticker do contrato (ex: 'DI1F26')
            codigo_isin: Código ISIN do contrato (opcional)
            data_vencimento: Data de vencimento no formato 'YYYY-MM-DD' (opcional)
            
        Returns:
            Ticker do contrato (sempre o mesmo que foi passado).
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
    # OPERAÇÕES DE CONSULTA (Datas)
    # ============================================================================
    
    def get_max_date(self, table: str, date_col: str) -> Optional[str]:
        """
        Retorna a data máxima de uma coluna em uma tabela.
        
        Args:
            table: Nome da tabela
            date_col: Nome da coluna de data
            
        Returns:
            Data máxima no formato 'YYYY-MM-DD' ou None se a tabela estiver vazia.
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
        Retorna lista de datas faltantes em uma tabela.
        
        Regra:
        - Se a tabela tem datas: começa no dia seguinte ao MAX(date_col)
        - Se não tem: começa em default_start
        
        Args:
            table: Nome da tabela
            date_col: Nome da coluna de data
            default_start: Data inicial padrão se a tabela estiver vazia
            end_date: Data final (default: ontem)
            skip_weekends: Se True, pula finais de semana
            
        Returns:
            Lista de datas no formato 'YYYY-MM-DD'.
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
        Última data de negócio com artefato não vazio na camada raw/silver.

        Distinto de get_max_date (Gold/SQLite): reflete o que a extração já obteve.
        """
        from rf_lake.watermarks import get_watermark

        return get_watermark(dataset, layer)

    def get_freshness_summary(self) -> "pd.DataFrame":
        """
        Resumo por dataset: última data bronze, silver e Gold (MAX no SQLite).
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
    # OPERAÇÕES DIRETAS COM REPOSITÓRIOS (Acesso Avançado)
    # ============================================================================
    
    @contextmanager
    def transaction(self):
        """
        Context manager para executar operações em uma transação.
        
        Útil quando você precisa fazer múltiplas operações atômicas.
        
        Exemplo:
            with db.transaction() as conn:
                # Múltiplas operações usando conn diretamente
                TitulosPublicosRepo.get_or_create(conn, ...)
                LiquidacoesMercadoRepo.upsert(conn, ...)
                # Commit automático ao sair do contexto
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
        Executa uma query SQL e retorna os resultados.
        
        ATENÇÃO: Use com cuidado. Prefira os métodos específicos quando possível.
        
        Args:
            sql: Query SQL
            params: Parâmetros para a query (tupla)
            
        Returns:
            Lista de tuplas com os resultados.
        """
        with self._get_connection() as conn:
            return conn.execute(sql, params).fetchall()
    
    def execute_update(self, sql: str, params: tuple = ()) -> int:
        """
        Executa uma atualização SQL (INSERT, UPDATE, DELETE).
        
        ATENÇÃO: Use com cuidado. Prefira os métodos específicos quando possível.
        
        Args:
            sql: Query SQL
            params: Parâmetros para a query (tupla)
            
        Returns:
            Número de linhas afetadas.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor.rowcount
