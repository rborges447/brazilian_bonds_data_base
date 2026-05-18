"""
UpToData client (local CSV files).
"""

from __future__ import annotations

import os
import time
import traceback
from datetime import datetime
from pathlib import Path

import pandas as pd

from rf_lake.logging import get_logger
from rf_lake.settings import UPTODATA_PASTA_INTEREST_RATE_BASE, UPTODATA_ARQUIVO_INTEREST_RATE_BASE

logger = get_logger(__name__)

# Defaults (can be overridden via settings)
PASTA_INTEREST_RATE_BASE = UPTODATA_PASTA_INTEREST_RATE_BASE or "x:\\Interest_Rate\\SettlementPrice"
PASTA_CURRENCY_BASE = "X:\\Currency\\SettlementPrice"

ARQUIVO_INTEREST_RATE_BASE = UPTODATA_ARQUIVO_INTEREST_RATE_BASE or "Interest_Rate_SettlementPriceFile_Futures_"
ARQUIVO_CURRENCY_BASE = "Currency_SettlementPriceFile_Futures_"


def definir_caminho_adj_bmf(pasta_base: str, arquivo_base: str, data_str: str) -> str | None:
    """
    Pick the newest file by modification time for a business date.

    Args:
        pasta_base: Base folder path
        arquivo_base: Filename prefix
        data_str: Date string "YYYY-MM-DD" (e.g. "2026-08-15")

    Returns:
        Full path to newest matching file, or None if not found
    """
    try:
        dt = datetime.strptime(data_str, "%Y-%m-%d")

        dia = f"{dt.day:02}"
        mes = f"{dt.month:02}"
        ano = str(dt.year)

        pasta = pasta_base + f'\\{ano}{mes}{dia}\\'
        prefixo = arquivo_base + f'{ano}{mes}{dia}_'

        if not os.path.exists(pasta):
            logger.warning(f"Folder not found: {pasta}")
            return None

        arquivos = os.listdir(pasta)

        arquivos_filtrados = [
            f for f in arquivos
            if f.startswith(prefixo) and f.endswith(".csv")
        ]

        if not arquivos_filtrados:
            logger.warning(f"No files with prefix {prefixo} in {pasta}")
            return None

        arquivos_com_data = []
        for arq in arquivos_filtrados:
            caminho_completo = os.path.join(pasta, arq)
            if os.path.exists(caminho_completo):
                mtime = os.path.getmtime(caminho_completo)
                arquivos_com_data.append((mtime, arq, caminho_completo))

        if not arquivos_com_data:
            logger.warning(f"No valid files in folder {pasta}")
            return None

        arquivo_mais_recente = max(arquivos_com_data, key=lambda x: x[0])

        logger.info(f"Found {len(arquivos_filtrados)} files with prefix {prefixo}")
        logger.info(f"Using newest file: {arquivo_mais_recente[1]}")

        return arquivo_mais_recente[2]

    except Exception as e:
        logger.error(f"Unexpected error resolving path: {e}")
        traceback.print_exc()
        return None


def scrap_ajustes_bmf(data: str, pasta_base: str = PASTA_INTEREST_RATE_BASE, arquivo_base: str = ARQUIVO_INTEREST_RATE_BASE) -> pd.DataFrame:
    """
    Load BMF adjustments for one date.

    Args:
        data: "YYYY-MM-DD" (e.g. "2026-08-15")
        pasta_base: Base folder (default: PASTA_INTEREST_RATE_BASE)
        arquivo_base: File prefix (default: ARQUIVO_INTEREST_RATE_BASE)

    Returns:
        pandas.DataFrame from the CSV
    """
    caminho = definir_caminho_adj_bmf(pasta_base, arquivo_base, data)

    if caminho is None:
        return pd.DataFrame()

    return pd.read_csv(caminho, sep=";")


def scrap_ajustes_bmf_for_dates(pasta_base: str, arquivo_base: str, lista_datas: list[str]) -> pd.DataFrame:
    """
    Load multiple dates and concatenate into one DataFrame.

    Args:
        pasta_base: Base folder (e.g. PASTA_INTEREST_RATE_BASE)
        arquivo_base: File prefix (e.g. ARQUIVO_INTEREST_RATE_BASE)
        lista_datas: List of "YYYY-MM-DD" strings

    Returns:
        Combined DataFrame, or empty if nothing found
    """
    dfs = []

    for data_str in lista_datas:
        try:
            logger.info(f"Processing date: {data_str}")

            caminho = definir_caminho_adj_bmf(pasta_base, arquivo_base, data_str)

            if caminho is None:
                logger.warning(f"Skipping {data_str} — file not found")
                continue

            df_temp = pd.read_csv(caminho, sep=";")

            if 'RptDt' not in df_temp.columns and 'data_referencia' not in df_temp.columns:
                df_temp['data_referencia'] = data_str

            dfs.append(df_temp)
            logger.info(f"Date {data_str} loaded OK. {len(df_temp)} rows.")

        except Exception as e:
            logger.error(f"Error processing {data_str}: {e}")
            traceback.print_exc()
            continue

    if dfs:
        df_final = pd.concat(dfs, ignore_index=True)
        logger.info(f"Total rows in combined frame: {len(df_final)}")
        return df_final
    else:
        logger.warning("No files processed. Returning empty DataFrame.")
        return pd.DataFrame()
