"""
Cliente para dados UpToData (arquivos locais).
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

# Constantes padrão (podem ser sobrescritas via settings)
PASTA_INTEREST_RATE_BASE = UPTODATA_PASTA_INTEREST_RATE_BASE or "x:\\Interest_Rate\\SettlementPrice"
PASTA_CURRENCY_BASE = "X:\\Currency\\SettlementPrice"

ARQUIVO_INTEREST_RATE_BASE = UPTODATA_ARQUIVO_INTEREST_RATE_BASE or "Interest_Rate_SettlementPriceFile_Futures_"
ARQUIVO_CURRENCY_BASE = "Currency_SettlementPriceFile_Futures_"


def definir_caminho_adj_bmf(pasta_base: str, arquivo_base: str, data_str: str) -> str | None:
    """
    Busca o arquivo mais recente por data de modificação.
    
    Args:
        pasta_base: Caminho base da pasta
        arquivo_base: Prefixo base do arquivo
        data_str: String no formato "AAAA-MM-DD" (ex: "2026-08-15")
    
    Returns:
        Caminho completo do arquivo mais recente ou None se não encontrado
    """
    try:
        # Converter string para datetime
        data = datetime.strptime(data_str, "%Y-%m-%d")
        
        # Convertendo para string formatada
        dia = f"{data.day:02}"
        mes = f"{data.month:02}"
        ano = str(data.year)

        # Pasta
        pasta = pasta_base + f'\\{ano}{mes}{dia}\\'

        # Prefixo fixo do arquivo
        prefixo = arquivo_base + f'{ano}{mes}{dia}_'

        # Verifica se a pasta existe
        if not os.path.exists(pasta):
            logger.warning(f"Pasta não encontrada: {pasta}")
            return None

        # Lista todos arquivos
        arquivos = os.listdir(pasta)

        # Filtra os que começam com prefixo e terminam com .csv
        arquivos_filtrados = [
            f for f in arquivos
            if f.startswith(prefixo) and f.endswith(".csv")
        ]

        if not arquivos_filtrados:
            logger.warning(f"Nenhum arquivo encontrado com prefixo {prefixo} na pasta {pasta}")
            return None

        # Busca o arquivo mais recente por data de modificação
        arquivos_com_data = []
        for arq in arquivos_filtrados:
            caminho_completo = os.path.join(pasta, arq)
            if os.path.exists(caminho_completo):
                mtime = os.path.getmtime(caminho_completo)
                arquivos_com_data.append((mtime, arq, caminho_completo))

        if not arquivos_com_data:
            logger.warning(f"Nenhum arquivo válido encontrado na pasta {pasta}")
            return None

        # Pega o arquivo com maior data de modificação (mais recente)
        arquivo_mais_recente = max(arquivos_com_data, key=lambda x: x[0])
        
        logger.info(f"Encontrados {len(arquivos_filtrados)} arquivos com prefixo {prefixo}")
        logger.info(f"Arquivo mais recente selecionado: {arquivo_mais_recente[1]}")

        return arquivo_mais_recente[2]  # Retorna caminho completo
    
    except Exception as e:
        logger.error(f"Erro inesperado ao definir caminho: {e}")
        traceback.print_exc()
        return None


def scrap_ajustes_bmf(data: str, pasta_base: str = PASTA_INTEREST_RATE_BASE, arquivo_base: str = ARQUIVO_INTEREST_RATE_BASE) -> pd.DataFrame:
    """
    Busca dados de ajustes BMF para uma data específica.
    
    Args:
        data: String no formato "AAAA-MM-DD" (ex: "2026-08-15")
        pasta_base: Caminho base da pasta (padrão: PASTA_INTEREST_RATE_BASE)
        arquivo_base: Prefixo base do arquivo (padrão: ARQUIVO_INTEREST_RATE_BASE)
    
    Returns:
        pandas.DataFrame com os dados do arquivo
    """
    caminho = definir_caminho_adj_bmf(pasta_base, arquivo_base, data)
    
    if caminho is None:
        return pd.DataFrame()
    
    return pd.read_csv(caminho, sep=";")


def scrap_ajustes_bmf_for_dates(pasta_base: str, arquivo_base: str, lista_datas: list[str]) -> pd.DataFrame:
    """
    Processa múltiplas datas e retorna um único DataFrame com todos os dados.
    
    Args:
        pasta_base: Caminho base da pasta (ex: PASTA_INTEREST_RATE_BASE)
        arquivo_base: Prefixo base do arquivo (ex: ARQUIVO_INTEREST_RATE_BASE)
        lista_datas: Lista de strings no formato "AAAA-MM-DD" (ex: ["2026-08-15", "2026-08-16"])
    
    Returns:
        DataFrame com todos os dados concatenados. DataFrame vazio se nenhum arquivo for encontrado.
    """
    dfs = []
    
    for data_str in lista_datas:
        try:
            logger.info(f"Processando data: {data_str}")
            
            # Busca o caminho do arquivo
            caminho = definir_caminho_adj_bmf(pasta_base, arquivo_base, data_str)
            
            if caminho is None:
                logger.warning(f"Pulando data {data_str} - arquivo não encontrado")
                continue
            
            # Lê o CSV
            df_temp = pd.read_csv(caminho, sep=";")
            
            # Se não houver coluna RptDt (que será renomeada para data_referencia),
            # adiciona data_referencia manualmente usando a data do arquivo
            if 'RptDt' not in df_temp.columns and 'data_referencia' not in df_temp.columns:
                df_temp['data_referencia'] = data_str
            
            dfs.append(df_temp)
            logger.info(f"Data {data_str} processada com sucesso. {len(df_temp)} registros.")
            
        except Exception as e:
            logger.error(f"Erro ao processar data {data_str}: {e}")
            traceback.print_exc()
            continue
    
    # Concatena todos os DataFrames
    if dfs:
        df_final = pd.concat(dfs, ignore_index=True)
        logger.info(f"Total de registros no DataFrame final: {len(df_final)}")
        return df_final
    else:
        logger.warning("Nenhum arquivo foi encontrado/processado. Retornando DataFrame vazio.")
        return pd.DataFrame()
