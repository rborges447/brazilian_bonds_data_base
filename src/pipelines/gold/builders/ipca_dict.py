"""Build IPCA dict (daily as_of) from silver ``ipca_indice`` + ``projecoes`` + feriados."""

from __future__ import annotations

import pandas as pd

BUILDER_NAME = "ipca_dict"
SILVER_DATASETS = ("ipca_indice", "projecoes")

# Legado NTN-B; futuramente pode vir de série histórica
INDICE_IPCA_DATA_BASE = 1614.62
N_LOOKBACK_MONTHS = 3


def _month_start(as_of: str | pd.Timestamp) -> pd.Timestamp:
    ts = pd.Timestamp(as_of).normalize()
    return ts.replace(day=1)


def _ref_month_column(df: pd.DataFrame) -> str:
    if "ref_month" in df.columns:
        return "ref_month"
    if "reference_month" in df.columns:
        return "reference_month"
    raise ValueError(
        f"Frame must have ref_month or reference_month, got: {list(df.columns)}"
    )


def slice_monthly_frames(
    full: pd.DataFrame,
    as_of: str | pd.Timestamp,
    n: int = N_LOOKBACK_MONTHS,
) -> pd.DataFrame:
    """Last ``n`` non-empty monthly partitions with ref_month <= month(as_of)."""
    if full is None or full.empty:
        return pd.DataFrame()
    col = _ref_month_column(full)
    monthly = full.copy()
    monthly[col] = pd.to_datetime(monthly[col], errors="coerce").dt.normalize()
    monthly = monthly[monthly[col].notna()]
    limite = _month_start(as_of)
    cand = monthly[monthly[col] <= limite]
    if cand.empty:
        return pd.DataFrame()
    parts = sorted(cand[col].drop_duplicates().unique(), reverse=True)[:n]
    return cand[cand[col].isin(parts)].reset_index(drop=True)


def e_dia_util(data: pd.Timestamp | str, feriados: set[str]) -> bool:
    ts = pd.Timestamp(data).normalize()
    if ts.weekday() >= 5:
        return False
    return ts.strftime("%Y-%m-%d") not in feriados


def adicionar_dias_uteis(
    data: pd.Timestamp | str,
    n_dias: int,
    feriados: set[str],
) -> pd.Timestamp:
    cur = pd.Timestamp(data).normalize()
    step = 1 if n_dias >= 0 else -1
    remaining = abs(int(n_dias))
    while remaining > 0:
        cur += pd.Timedelta(days=step)
        if e_dia_util(cur, feriados):
            remaining -= 1
    return cur.normalize()


def inicio_fim_mes_ipca(
    data: pd.Timestamp | str,
    feriados: set[str],
) -> tuple[pd.Timestamp, pd.Timestamp]:
    data = pd.Timestamp(data).normalize()
    dia_15 = {
        "ant": (data - pd.DateOffset(months=1)).replace(day=15).normalize(),
        "atu": data.replace(day=15).normalize(),
        "prox": (data + pd.DateOffset(months=1)).replace(day=15).normalize(),
    }
    for key in dia_15:
        if not e_dia_util(dia_15[key], feriados):
            dia_15[key] = adicionar_dias_uteis(dia_15[key], 1, feriados)
    if data < dia_15["atu"]:
        return dia_15["ant"], dia_15["atu"]
    return dia_15["atu"], dia_15["prox"]


def projecao_mais_recente(
    df_proj: pd.DataFrame,
    as_of: str | pd.Timestamp,
    *,
    indice: str | None = "IPCA",
    tipo_projecao: str | None = "PROJEÇÕES PARA O MÊS CORRENTE",
    ref_month: str | pd.Timestamp | None = None,
    respeitar_validade: bool = False,
) -> pd.Series:
    """Projeção com data_coleta <= as_of (maior data_coleta entre as válidas)."""
    as_of = pd.Timestamp(as_of).normalize()
    sub = df_proj.copy()

    if indice is not None:
        sub = sub[sub["indice"].astype(str).str.upper() == indice.upper()]
    if tipo_projecao is not None:
        sub = sub[sub["tipo_projecao"] == tipo_projecao]
    if ref_month is not None:
        mes = pd.Timestamp(ref_month).strftime("%Y-%m-%d")[:7] + "-01"
        sub = sub[sub["ref_month"].astype(str).str[:10] == mes]

    sub["data_coleta"] = pd.to_datetime(sub["data_coleta"], errors="coerce").dt.normalize()
    sub = sub[sub["data_coleta"].notna() & (sub["data_coleta"] <= as_of)]

    if respeitar_validade and "data_validade" in sub.columns:
        val = pd.to_datetime(sub["data_validade"], errors="coerce").dt.normalize()
        sub = sub[val.isna() | (val >= as_of)]

    if sub.empty:
        raise ValueError(f"Nenhuma projeção com data_coleta <= {as_of.date()}")

    return sub.loc[sub["data_coleta"].idxmax()]


def projecao_mais_recente_valor(
    df_proj: pd.DataFrame,
    as_of: str | pd.Timestamp,
    **kwargs: object,
) -> tuple[float, pd.Timestamp]:
    row = projecao_mais_recente(df_proj, as_of, **kwargs)
    return (
        float(row["variacao_projetada"]),
        pd.Timestamp(row["data_coleta"]).normalize(),
    )


def ipca_fechado_from_monthly(
    ipca_monthly: pd.DataFrame,
    as_of: pd.Timestamp | str,
    data_coleta: pd.Timestamp | str,
) -> dict[str, float | int | str]:
    """
    IPCA fechado conforme divulgação.

    ``data_coleta`` (ex. da ANBIMA): quando o índice de M-1 em relação a essa data
    passa a estar disponível. Se ``as_of >= data_coleta`` usa esse mês; senão o anterior.
    """
    as_of = pd.Timestamp(as_of).normalize()
    div = pd.Timestamp(data_coleta).normalize()

    mes_indice_na_div = div.replace(day=1) - pd.DateOffset(months=1)
    ultimo_ref = (
        mes_indice_na_div
        if as_of >= div
        else mes_indice_na_div - pd.DateOffset(months=1)
    )
    anterior_ref = ultimo_ref - pd.DateOffset(months=1)

    monthly = ipca_monthly.copy()
    monthly["ref_month"] = pd.to_datetime(monthly["ref_month"], errors="coerce").dt.normalize()
    monthly = monthly.sort_values("ref_month").reset_index(drop=True)

    def _pick(ref: pd.Timestamp) -> pd.Series:
        rows = monthly[monthly["ref_month"] == ref]
        if rows.empty:
            raise KeyError(f"ipca_indice sem ref_month {ref:%Y-%m-%d}")
        return rows.iloc[-1]

    row_atual = _pick(ultimo_ref)
    try:
        row_ant = _pick(anterior_ref)
    except KeyError:
        i = int(monthly.index[monthly["ref_month"] == ultimo_ref][0])
        row_ant = monthly.iloc[i - 1] if i > 0 else row_atual

    return {
        "ULTIMO_MES_IPCA": int(row_atual["ref_month"].month),
        "REF_MONTH_ATUAL": row_atual["ref_month"].strftime("%Y-%m-%d"),
        "REF_MONTH_ANTERIOR": row_ant["ref_month"].strftime("%Y-%m-%d"),
        "DATA_COLETA_REFERENCIA": div.strftime("%Y-%m-%d"),
        "INDICE_IPCA_FECHADO_ATUAL": float(row_atual["ipca_index"]),
        "INDICE_IPCA_FECHADO_ANTERIOR": float(row_ant["ipca_index"]),
        "VAR_IPCA_ATUAL": float(row_atual["ipca_mom"]),
        "VAR_IPCA_ANTERIOR": float(row_ant["ipca_mom"]),
    }


def dicionario_ipca(
    as_of: pd.Timestamp | str,
    fechado: dict[str, float | int | str],
    ipca_proj_float: float,
    *,
    ipca_proj_data_coleta: pd.Timestamp | str | None = None,
    feriados: set[str],
) -> dict[str, float | int | str | bool]:
    """
    Monta o dict gold do IPCA.

    ``usa_fechado`` quando o último mês fechado é M-1 da data e a data está antes
    do dia 15 útil do mês corrente; senão usa projeção.
    """
    data = pd.Timestamp(as_of).normalize()
    dia_15_mes_atu = data.replace(day=15).normalize()
    if not e_dia_util(dia_15_mes_atu, feriados):
        dia_15_mes_atu = adicionar_dias_uteis(dia_15_mes_atu, 1, feriados)
    mes_m1 = (data - pd.DateOffset(months=1)).replace(day=1)
    ref_atual = pd.Timestamp(fechado["REF_MONTH_ATUAL"])
    usa_fechado = (
        ref_atual == mes_m1
        and data < dia_15_mes_atu
        and float(fechado["INDICE_IPCA_FECHADO_ATUAL"])
        != float(fechado["INDICE_IPCA_FECHADO_ANTERIOR"])
    )
    if usa_fechado:
        ipca_usado = (
            float(fechado["INDICE_IPCA_FECHADO_ATUAL"])
            / float(fechado["INDICE_IPCA_FECHADO_ANTERIOR"])
            - 1
        ) * 100
    else:
        ipca_usado = float(ipca_proj_float)
    out: dict[str, float | int | str | bool] = {
        "ULTIMO_MES_IPCA": int(fechado["ULTIMO_MES_IPCA"]),
        "REF_MONTH_ATUAL": str(fechado["REF_MONTH_ATUAL"]),
        "REF_MONTH_ANTERIOR": str(fechado["REF_MONTH_ANTERIOR"]),
        "INDICE_IPCA_DATA_BASE": INDICE_IPCA_DATA_BASE,
        "INDICE_IPCA_FECHADO_ATUAL": float(fechado["INDICE_IPCA_FECHADO_ATUAL"]),
        "INDICE_IPCA_FECHADO_ANTERIOR": float(fechado["INDICE_IPCA_FECHADO_ANTERIOR"]),
        "VAR_IPCA_ATUAL": float(fechado["VAR_IPCA_ATUAL"]),
        "VAR_IPCA_ANTERIOR": float(fechado["VAR_IPCA_ANTERIOR"]),
        "IPCA_PROJ": float(ipca_proj_float),
        "IPCA_USADO": float(ipca_usado),
        "USA_FECHADO": usa_fechado,
        "DATA_COLETA_REFERENCIA": str(fechado["DATA_COLETA_REFERENCIA"]),
    }
    if ipca_proj_data_coleta is not None:
        out["IPCA_PROJ_DATA_COLETA"] = pd.Timestamp(ipca_proj_data_coleta).strftime(
            "%Y-%m-%d"
        )
    return out


def build_for_date(
    as_of: str | pd.Timestamp,
    *,
    ipca_monthly: pd.DataFrame,
    projecoes: pd.DataFrame,
    feriados: set[str],
    n_lookback_months: int = N_LOOKBACK_MONTHS,
) -> dict[str, float | int | str | bool]:
    """Build IPCA dict for one daily ``as_of`` from pre-loaded silver frames."""
    data = pd.Timestamp(as_of).normalize()
    ipca_slice = slice_monthly_frames(ipca_monthly, data, n_lookback_months)
    proj_slice = slice_monthly_frames(projecoes, data, n_lookback_months)
    if ipca_slice.empty:
        raise ValueError(f"ipca_indice sem dados até {data.date()}")
    if proj_slice.empty:
        raise ValueError(f"projecoes sem dados até {data.date()}")

    inicio, fim = inicio_fim_mes_ipca(data, feriados)
    ipca_proj, data_coleta_proj = projecao_mais_recente_valor(
        proj_slice,
        data,
        respeitar_validade=False,
    )
    fechado = ipca_fechado_from_monthly(
        ipca_slice,
        data,
        data_coleta=data_coleta_proj,
    )
    out = dicionario_ipca(
        data,
        fechado,
        ipca_proj,
        ipca_proj_data_coleta=data_coleta_proj,
        feriados=feriados,
    )
    out["INICIO_MES_IPCA"] = inicio.strftime("%Y-%m-%d")
    out["FIM_MES_IPCA"] = fim.strftime("%Y-%m-%d")
    return out
