"""
Cliente para API BCB (Banco Central do Brasil).
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Iterable, List, Union

import pandas as pd

from rf_lake.logging import get_logger

logger = get_logger(__name__)

# Base URL para negociações do BCB
DEFAULT_BASE_URL = "https://www4.bcb.gov.br/pom/demab/negociacoes/download"


def _ensure_date(data_ref: Union[str, date]) -> date:
    """
    Converte a entrada para datetime.date.
    Aceita:
      - str no formato 'AAAA-MM-DD'
      - datetime.date
    """
    if isinstance(data_ref, date):
        return data_ref
    if isinstance(data_ref, str):
        try:
            return datetime.strptime(data_ref, "%Y-%m-%d").date()
        except ValueError as e:
            raise ValueError("data_ref deve estar no formato 'AAAA-MM-DD' (ex.: '2025-08-01').") from e
    raise TypeError("data_ref deve ser str ('AAAA-MM-DD') ou datetime.date.")


def format_ano_mes(data_ref: Union[str, date]) -> str:
    """
    Formata a data no padrão AAAAMM, usado pelo arquivo do Bacen (NegE{AAAAMM}.ZIP).
    Ex.: 2025-08-15 -> '202508'
    """
    dt = _ensure_date(data_ref)
    return f"{dt.year}{dt.month:02d}"


def build_negociacoes_url(data_ref: Union[str, date], base_url: str = DEFAULT_BASE_URL) -> str:
    """
    Constrói a URL final do Bacen para o arquivo ZIP de negociações do mês da data fornecida.

    Entrada:
      - data_ref: 'AAAA-MM-DD' (str) ou datetime.date
      - base_url: URL base (padrão: DEFAULT_BASE_URL)

    Retorno:
      - URL no formato: {base_url}/NegE{AAAAMM}.ZIP

    Exemplo:
      build_negociacoes_url("2025-08-15")
      -> 'https://www4.bcb.gov.br/pom/demab/negociacoes/download/NegE202508.ZIP'
    """
    ano_mes = format_ano_mes(data_ref)
    return f"{base_url}/NegE{ano_mes}.ZIP"


def fetch_negociacoes_bruto_por_datas(
    datas: Iterable[Union[str, date]],
    sep: str = ";",
    encoding: str = "latin-1",
    compression: str = "zip",
    date_column: str | None = None,
    base_url: str = DEFAULT_BASE_URL,
) -> pd.DataFrame:
    """
    Lê, de forma bruta, os arquivos de negociações do Bacen (NegE{AAAAMM}.ZIP)
    para uma lista de datas e filtra para retornar apenas as datas solicitadas.
    
    NÃO aplica nenhum tratamento/transformação além da filtragem por data:
    - Não faz parse de datas (exceto para filtro)
    - Não renomeia colunas
    - Não adiciona colunas auxiliares
    - Não ajusta tipos

    Regras:
      - Agrupa datas por mês (evita baixar o mesmo arquivo múltiplas vezes)
      - Para cada mês único, baixa o arquivo ZIP uma vez
      - Filtra o DataFrame para manter apenas as datas fornecidas
      - Se a leitura falhar (404/erro rede/arquivo vazio), loga um aviso e segue
      - Concatena apenas os DataFrames válidos filtrados
      - Se nenhuma data retornar dados, retorna DataFrame vazio

    Parâmetros:
      datas: iterável de 'YYYY-MM-DD' (str) ou datetime.date
      sep: separador do CSV interno (padrão ';')
      encoding: encoding do CSV interno (padrão 'latin-1')
      compression: tipo de compressão (padrão 'zip', pois o endpoint é .ZIP)
      date_column: nome da coluna de data (None = auto-detecta)
      base_url: URL base para downloads

    Retorno:
      DataFrame bruto concatenado, filtrado apenas para as datas fornecidas.
    """
    # Normaliza datas e cria conjunto para filtro rápido
    target_dates = {_ensure_date(d) for d in datas}
    if not target_dates:
        return pd.DataFrame()
    
    # Agrupa datas por mês (ano-mês) para evitar downloads duplicados
    dates_by_month: defaultdict[tuple[int, int], list[date]] = defaultdict(list)
    
    for dt in target_dates:
        dates_by_month[(dt.year, dt.month)].append(dt)
    
    frames: List[pd.DataFrame] = []
    
    def _parse_dates_disambiguate_slash(series: pd.Series, allowed: set[date]) -> pd.Series:
        """
        Parseia datas com possível ambiguidade DD/MM vs MM/DD escolhendo, por linha,
        o parse que cai em `allowed`.

        Motivação: algumas colunas (ex.: DATA MOV) podem vir como '08/01/2017' e
        precisamos garantir que as datas solicitadas (allowed) sejam respeitadas.
        """
        s = series.copy()
        # manter NaNs; converter o resto para string
        s_str = s.astype("string").str.strip()
        s_str = s_str.where(s_str.notna() & (s_str != ""), other=pd.NA)

        # Tentativas de parse explícitas (mais baratas e determinísticas)
        dt_dmy = pd.to_datetime(s_str, format="%d/%m/%Y", errors="coerce")
        dt_mdy = pd.to_datetime(s_str, format="%m/%d/%Y", errors="coerce")
        dt_iso = pd.to_datetime(s_str, format="%Y-%m-%d", errors="coerce")

        # Preferir ISO quando aplicável
        chosen = dt_iso.copy()

        # Para barras, escolher pelo que cai em `allowed`
        dmy_ok = dt_dmy.dt.date.isin(allowed)
        mdy_ok = dt_mdy.dt.date.isin(allowed)

        # Regras:
        # - se DMY bate allowed, usa DMY
        # - senão, se MDY bate allowed, usa MDY
        # - senão, se uma das duas parseou e a outra não, usa a que parseou
        # - senão, deixa como NaT (será descartado no filtro)
        chosen = chosen.where(~dmy_ok, dt_dmy)
        chosen = chosen.where(dmy_ok | ~mdy_ok, dt_mdy)

        fallback = dt_dmy.combine_first(dt_mdy)
        chosen = chosen.combine_first(fallback)

        return chosen

    # Processa cada mês único
    for (year, month), month_dates in dates_by_month.items():
        # Usa qualquer data do mês para construir a URL
        sample_date = month_dates[0]
        url = build_negociacoes_url(sample_date, base_url)
        
        try:
            df_month = pd.read_csv(url, sep=sep, encoding=encoding, compression=compression)
        except Exception as ex:
            logger.warning("Bacen: falha ao ler %s: %s", url, ex)
            continue
        
        if df_month is None or df_month.empty:
            logger.warning("Bacen: retorno vazio para %s", url)
            continue
        
        # Auto-detecta coluna de data se não fornecida
        date_col = date_column
        if date_col is None:
            # Tenta encontrar coluna de data (case-insensitive)
            possible_names = ['data', 'DATA', 'Data Negociação', 'DataNegociacao', 
                            'data_negociacao', 'DtNeg', 'dt_neg']
            for col in df_month.columns:
                if col.strip() in possible_names or 'data' in col.lower():
                    date_col = col
                    break
        
        if date_col is None or date_col not in df_month.columns:
            logger.warning(
                "Bacen: coluna de data não encontrada em %s. Colunas: %s",
                url,
                list(df_month.columns),
            )
            # Se o chamador informou explicitamente a coluna de data e ela não existe,
            # não é seguro retornar o mês inteiro: não conseguimos filtrar pelas datas.
            if date_column is not None:
                continue
            # Caso contrário, mantém o comportamento antigo (retorna tudo).
            frames.append(df_month)
            continue
        
        # Filtra apenas as datas solicitadas
        # Tenta diferentes formatos de data na coluna
        allowed = set(month_dates)
        df_month[date_col] = _parse_dates_disambiguate_slash(df_month[date_col], allowed)
        df_month["_date_only"] = df_month[date_col].dt.date
        
        # Filtra apenas as datas do mês que estão na lista
        df_filtered = df_month[df_month['_date_only'].isin(month_dates)].copy()
        df_filtered = df_filtered.drop(columns=['_date_only'])
        
        if not df_filtered.empty:
            frames.append(df_filtered)
    
    if not frames:
        logger.info("Bacen: nenhuma data retornou dados após filtro; DataFrame final vazio.")
        return pd.DataFrame()
    
    return pd.concat(frames, ignore_index=True, sort=False)
