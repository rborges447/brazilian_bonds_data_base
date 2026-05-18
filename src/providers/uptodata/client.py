"""UpToData client (local CSV files)."""

from __future__ import annotations

import logging
import os
import traceback
from datetime import datetime

import pandas as pd

from config import UptodataSettings, get_settings

logger = logging.getLogger(__name__)


def _resolve_uptodata_paths(
    settings: UptodataSettings | None = None,
) -> tuple[str, str]:
    cfg = settings or get_settings().uptodata
    pasta = cfg.pasta_interest_rate_base.strip()
    arquivo = cfg.arquivo_interest_rate_base.strip()
    if not pasta or not arquivo:
        logger.warning(
            "UpToData: UPTODATA_PASTA_INTEREST_RATE_BASE and "
            "UPTODATA_ARQUIVO_INTEREST_RATE_BASE must be set for BMF adjustments."
        )
    return pasta, arquivo


def definir_caminho_adj_bmf(
    pasta_base: str,
    arquivo_base: str,
    data_str: str,
) -> str | None:
    """Pick the newest file by modification time for a business date."""
    if not pasta_base or not arquivo_base:
        return None

    try:
        dt = datetime.strptime(data_str, "%Y-%m-%d")
        dia = f"{dt.day:02}"
        mes = f"{dt.month:02}"
        ano = str(dt.year)

        pasta = pasta_base + f"\\{ano}{mes}{dia}\\"
        prefixo = arquivo_base + f"{ano}{mes}{dia}_"

        if not os.path.exists(pasta):
            logger.warning("Folder not found: %s", pasta)
            return None

        arquivos = os.listdir(pasta)
        arquivos_filtrados = [
            f for f in arquivos if f.startswith(prefixo) and f.endswith(".csv")
        ]

        if not arquivos_filtrados:
            logger.warning("No files with prefix %s in %s", prefixo, pasta)
            return None

        arquivos_com_data = []
        for arq in arquivos_filtrados:
            caminho_completo = os.path.join(pasta, arq)
            if os.path.exists(caminho_completo):
                mtime = os.path.getmtime(caminho_completo)
                arquivos_com_data.append((mtime, arq, caminho_completo))

        if not arquivos_com_data:
            logger.warning("No valid files in folder %s", pasta)
            return None

        arquivo_mais_recente = max(arquivos_com_data, key=lambda x: x[0])
        logger.info("Found %s files with prefix %s", len(arquivos_filtrados), prefixo)
        logger.info("Using newest file: %s", arquivo_mais_recente[1])
        return arquivo_mais_recente[2]

    except Exception as exc:
        logger.error("Unexpected error resolving path: %s", exc)
        traceback.print_exc()
        return None


def scrap_ajustes_bmf(
    data: str,
    pasta_base: str | None = None,
    arquivo_base: str | None = None,
    settings: UptodataSettings | None = None,
) -> pd.DataFrame:
    cfg = settings or get_settings().uptodata
    pasta, arquivo = _resolve_uptodata_paths(cfg)
    pasta_use = pasta_base if pasta_base is not None else pasta
    arquivo_use = arquivo_base if arquivo_base is not None else arquivo

    caminho = definir_caminho_adj_bmf(pasta_use, arquivo_use, data)
    if caminho is None:
        return pd.DataFrame()
    return pd.read_csv(caminho, sep=";")


def scrap_ajustes_bmf_for_dates(
    lista_datas: list[str],
    pasta_base: str | None = None,
    arquivo_base: str | None = None,
    settings: UptodataSettings | None = None,
) -> pd.DataFrame:
    cfg = settings or get_settings().uptodata
    pasta, arquivo = _resolve_uptodata_paths(cfg)
    pasta_use = pasta_base if pasta_base is not None else pasta
    arquivo_use = arquivo_base if arquivo_base is not None else arquivo

    dfs: list[pd.DataFrame] = []
    for data_str in lista_datas:
        try:
            logger.info("Processing date: %s", data_str)
            caminho = definir_caminho_adj_bmf(pasta_use, arquivo_use, data_str)
            if caminho is None:
                logger.warning("Skipping %s — file not found", data_str)
                continue

            df_temp = pd.read_csv(caminho, sep=";")
            if "RptDt" not in df_temp.columns and "data_referencia" not in df_temp.columns:
                df_temp["data_referencia"] = data_str
            dfs.append(df_temp)
            logger.info("Date %s loaded OK. %s rows.", data_str, len(df_temp))
        except Exception as exc:
            logger.error("Error processing %s: %s", data_str, exc)
            traceback.print_exc()
            continue

    if dfs:
        df_final = pd.concat(dfs, ignore_index=True)
        logger.info("Total rows in combined frame: %s", len(df_final))
        return df_final

    logger.warning("No files processed. Returning empty DataFrame.")
    return pd.DataFrame()
