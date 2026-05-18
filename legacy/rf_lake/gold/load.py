"""
Gold: reads Silver (Parquet) and persists to SQLite (same repos as the legacy schema).
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from rf_lake.gold.db import get_conn
from rf_lake.gold.db.repositories import (
    AjustesBmfRepo,
    ContratosBmfRepo,
    FeriadosRepo,
    IpcaIndiceRepo,
    LeiloesRepo,
    LiquidacoesMercadoRepo,
    MercadoSecundarioRepo,
    ProjecoesRepo,
    TitulosPublicosRepo,
)
from rf_lake.gold.db.schema import PROJECOES_REQUIRED


def _parse_iso_date(d: str):
    return datetime.strptime(d, "%Y-%m-%d").date()


def _apply_dates_filter(
    df: pd.DataFrame,
    dates_filter: list[str] | None,
    date_col: str,
) -> pd.DataFrame:
    if not dates_filter or df.empty or date_col not in df.columns:
        return df
    return df[df[date_col].astype(str).isin(dates_filter)].copy()


def load_mercado_secundario(
    silver_path,
    dates_filter: list[str] | None = None,
) -> tuple[int, bool]:
    df = _apply_dates_filter(
        pd.read_parquet(silver_path), dates_filter, "data_referencia"
    )
    if df.empty:
        return 0, False
    required = ["tipo_titulo", "data_vencimento", "data_referencia"]
    if any(c not in df.columns for c in required):
        return 0, False
    conn = get_conn()
    try:
        for _, row in df.iterrows():
            tipo_titulo = str(row.get("tipo_titulo", ""))
            data_vencimento = str(row.get("data_vencimento", ""))
            TitulosPublicosRepo.get_or_create(
                conn=conn,
                tipo_titulo=tipo_titulo,
                data_vencimento=data_vencimento,
                expressao=row.get("expressao"),
                data_base=row.get("data_base"),
                codigo_selic=row.get("codigo_selic"),
                codigo_isin=row.get("codigo_isin"),
                status=row.get("status", "ATIVO"),
            )
            MercadoSecundarioRepo.upsert(
                conn=conn,
                tipo_titulo=tipo_titulo,
                data_vencimento=data_vencimento,
                data_referencia=str(row.get("data_referencia", "")),
                taxa_anbima=row.get("taxa_anbima"),
                intervalo_min_d0=row.get("intervalo_min_d0"),
                intervalo_max_d0=row.get("intervalo_max_d0"),
                intervalo_min_d1=row.get("intervalo_min_d1"),
                intervalo_max_d1=row.get("intervalo_max_d1"),
                pu=row.get("pu"),
            )
        conn.commit()
        return len(df), True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def load_liquidacoes_mercado(
    silver_path,
    dates_filter: list[str] | None = None,
) -> tuple[int, bool]:
    df = _apply_dates_filter(
        pd.read_parquet(silver_path), dates_filter, "data_referencia"
    )
    if df.empty:
        return 0, False
    required = ["tipo_titulo", "data_vencimento", "data_referencia"]
    if any(c not in df.columns for c in required):
        return 0, False
    conn = get_conn()
    try:
        for _, row in df.iterrows():
            tipo_titulo = str(row.get("tipo_titulo", ""))
            data_vencimento = str(row.get("data_vencimento", ""))
            TitulosPublicosRepo.get_or_create(
                conn=conn,
                tipo_titulo=tipo_titulo,
                data_vencimento=data_vencimento,
                expressao=row.get("expressao"),
                data_base=row.get("data_base"),
                codigo_selic=row.get("codigo_selic"),
                codigo_isin=row.get("codigo_isin"),
                status=row.get("status", "ATIVO"),
            )
            LiquidacoesMercadoRepo.upsert(
                conn=conn,
                tipo_titulo=tipo_titulo,
                data_vencimento=data_vencimento,
                data_referencia=str(row.get("data_referencia", "")),
                qtd_operacoes=row.get("qtd_operacoes"),
                qtd_titulos=row.get("qtd_titulos"),
                pu_medio=row.get("pu_medio"),
            )
        conn.commit()
        return len(df), True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def load_ajustes_bmf(
    silver_path,
    dates_filter: list[str] | None = None,
) -> tuple[int, bool]:
    df = _apply_dates_filter(
        pd.read_parquet(silver_path), dates_filter, "data_referencia"
    )
    if df.empty:
        return 0, False
    if any(c not in df.columns for c in ["ticker", "data_referencia"]):
        return 0, False
    conn = get_conn()
    try:
        for _, row in df.iterrows():
            ticker = ContratosBmfRepo.get_or_create(
                conn=conn,
                ticker=str(row.get("ticker", "")),
                codigo_isin=row.get("codigo_isin"),
                data_vencimento=row.get("data_vencimento"),
            )
            AjustesBmfRepo.upsert(
                conn=conn,
                ticker=ticker,
                data_referencia=str(row.get("data_referencia", "")),
                taxa_ajuste=row.get("taxa_ajuste"),
                quantidade_ajuste=row.get("quantidade_ajuste"),
            )
        conn.commit()
        return len(df), True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def load_leiloes(
    silver_path,
    dates_filter: list[str] | None = None,
) -> tuple[int, bool]:
    df = _apply_dates_filter(
        pd.read_parquet(silver_path), dates_filter, "data_referencia"
    )
    if df.empty:
        return 0, False
    required = ["numero_edital", "data_referencia", "tipo_titulo", "data_vencimento"]
    if any(c not in df.columns for c in required):
        return 0, False
    conn = get_conn()
    try:
        for _, row in df.iterrows():
            tipo_titulo = str(row.get("tipo_titulo", ""))
            data_vencimento = str(row.get("data_vencimento", ""))
            data_ref_str = str(row.get("data_referencia", ""))
            if not tipo_titulo or not data_vencimento or not data_ref_str:
                continue
            TitulosPublicosRepo.get_or_create(
                conn=conn,
                tipo_titulo=tipo_titulo,
                data_vencimento=data_vencimento,
                expressao=None,
                data_base=None,
                codigo_selic=None,
                codigo_isin=None,
                status="ATIVO",
            )
            numero_edital = int(row.get("numero_edital")) if pd.notna(row.get("numero_edital")) else None
            if numero_edital is None:
                continue
            LeiloesRepo.upsert(
                conn=conn,
                numero_edital=numero_edital,
                tipo_titulo=tipo_titulo,
                data_vencimento=data_vencimento,
                data_referencia=data_ref_str,
                oferta=int(row.get("oferta")) if pd.notna(row.get("oferta")) else None,
                quantidade_aceita=int(row.get("quantidade_aceita")) if pd.notna(row.get("quantidade_aceita")) else None,
                percentual_corte=float(row.get("percentual_corte")) if pd.notna(row.get("percentual_corte")) else None,
                oferta_segunda_volta=int(row.get("oferta_segunda_volta")) if pd.notna(row.get("oferta_segunda_volta")) else None,
                financeiro_aceito=float(row.get("financeiro_aceito")) if pd.notna(row.get("financeiro_aceito")) else None,
                financeiro_aceito_segunda_volta=float(row.get("financeiro_aceito_segunda_volta"))
                if pd.notna(row.get("financeiro_aceito_segunda_volta"))
                else None,
                quantidade_aceita_segunda_volta=int(row.get("quantidade_aceita_segunda_volta"))
                if pd.notna(row.get("quantidade_aceita_segunda_volta"))
                else None,
                pu_medio=float(row.get("pu_medio")) if pd.notna(row.get("pu_medio")) else None,
                taxa_media=float(row.get("taxa_media")) if pd.notna(row.get("taxa_media")) else None,
            )
        conn.commit()
        return len(df), True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def load_ipca_indice(
    silver_path,
    dates_filter: list[str] | None = None,
) -> tuple[int, bool]:
    df_monthly = pd.read_parquet(silver_path)
    if df_monthly.empty:
        return 0, False
    conn = get_conn()
    try:
        last_ref_month_iso = IpcaIndiceRepo.get_max_ref_month(conn)
        last_ref_month = _parse_iso_date(last_ref_month_iso) if last_ref_month_iso else None
        df_new = df_monthly
        if last_ref_month is not None and "ref_month" in df_new.columns:
            df_new = df_monthly[df_monthly["ref_month"] > last_ref_month].copy()
        if df_new.empty:
            conn.commit()
            return 0, True
        for _, row in df_new.iterrows():
            ref_month = row.get("ref_month")
            if pd.isna(ref_month):
                continue
            ref_month_iso = ref_month.isoformat() if hasattr(ref_month, "isoformat") else str(ref_month)[:10]
            ipca_index = float(row.get("ipca_index")) if pd.notna(row.get("ipca_index")) else None
            ipca_mom = float(row.get("ipca_mom")) if pd.notna(row.get("ipca_mom")) else None
            IpcaIndiceRepo.upsert(conn, ref_month=ref_month_iso, ipca_index=ipca_index, ipca_mom=ipca_mom)
        conn.commit()
        return int(len(df_new)), True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def load_projecoes(
    silver_path,
    dates_filter: list[str] | None = None,
) -> tuple[int, bool]:
    df = pd.read_parquet(silver_path)
    if df.empty:
        return 0, False
    missing = [c for c in PROJECOES_REQUIRED if c not in df.columns]
    if missing:
        return 0, False
    conn = get_conn()
    try:
        for _, row in df.iterrows():
            indice = str(row.get("indice", "")).strip()
            tipo_projecao = str(row.get("tipo_projecao", "")).strip()
            data_coleta = row.get("data_coleta")
            ref_month = str(row.get("ref_month", "")).strip()
            if not indice or not tipo_projecao or pd.isna(data_coleta) or not ref_month:
                continue
            data_coleta_str = str(data_coleta).strip() if pd.notna(data_coleta) else None
            if not data_coleta_str:
                continue
            variacao = row.get("variacao_projetada")
            variacao_projetada = float(variacao) if pd.notna(variacao) else None
            data_validade_raw = row.get("data_validade")
            data_validade_str = (
                str(data_validade_raw).strip()
                if pd.notna(data_validade_raw) and data_validade_raw is not None
                else None
            )
            ProjecoesRepo.upsert(
                conn,
                indice=indice,
                tipo_projecao=tipo_projecao,
                data_coleta=data_coleta_str,
                ref_month=ref_month,
                variacao_projetada=variacao_projetada,
                data_validade=data_validade_str,
            )
        conn.commit()
        return len(df), True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def load_feriados(
    silver_path,
    dates_filter: list[str] | None = None,
) -> tuple[int, bool]:
    df = pd.read_parquet(silver_path)
    if df.empty or "data" not in df.columns:
        return 0, False
    datas = df["data"].astype(str).tolist()
    conn = get_conn()
    try:
        FeriadosRepo.replace_all(conn, datas)
        conn.commit()
        return len(datas), True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


LOADERS = {
    "mercado_secundario": load_mercado_secundario,
    "liquidacoes_mercado": load_liquidacoes_mercado,
    "ajustes_bmf": load_ajustes_bmf,
    "leiloes": load_leiloes,
    "ipca_indice": load_ipca_indice,
    "projecoes": load_projecoes,
    "feriados": load_feriados,
}


def gold_from_silver(
    name: str,
    silver_path,
    dates_filter: list[str] | None = None,
) -> tuple[int, bool]:
    return LOADERS[name](silver_path, dates_filter=dates_filter)
