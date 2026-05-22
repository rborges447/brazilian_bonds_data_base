"""IPCA dict: builder dicts → DataFrame ready for SQL INSERT."""

from __future__ import annotations

import pandas as pd

IpcaDictRow = dict[str, float | int | str | bool]

IPCA_DICT_COLUMNS: tuple[str, ...] = (
    "data_referencia",
    "ultimo_mes_ipca",
    "ref_month_atual",
    "ref_month_anterior",
    "indice_ipca_data_base",
    "indice_ipca_fechado_atual",
    "indice_ipca_fechado_anterior",
    "var_ipca_atual",
    "var_ipca_ant",
    "ipca_proj",
    "ipca_usado",
    "usa_fechado",
    "data_coleta_referencia",
    "ipca_proj_data_coleta",
    "inicio_mes_ipca",
    "fim_mes_ipca",
)

_EMPTY = pd.DataFrame(columns=list(IPCA_DICT_COLUMNS))

_DICT_TO_COL: dict[str, str] = {
    "ULTIMO_MES_IPCA": "ultimo_mes_ipca",
    "REF_MONTH_ATUAL": "ref_month_atual",
    "REF_MONTH_ANTERIOR": "ref_month_anterior",
    "INDICE_IPCA_DATA_BASE": "indice_ipca_data_base",
    "INDICE_IPCA_FECHADO_ATUAL": "indice_ipca_fechado_atual",
    "INDICE_IPCA_FECHADO_ANTERIOR": "indice_ipca_fechado_anterior",
    "VAR_IPCA_ATUAL": "var_ipca_atual",
    "VAR_IPCA_ANTERIOR": "var_ipca_ant",
    "IPCA_PROJ": "ipca_proj",
    "IPCA_USADO": "ipca_usado",
    "USA_FECHADO": "usa_fechado",
    "DATA_COLETA_REFERENCIA": "data_coleta_referencia",
    "IPCA_PROJ_DATA_COLETA": "ipca_proj_data_coleta",
    "INICIO_MES_IPCA": "inicio_mes_ipca",
    "FIM_MES_IPCA": "fim_mes_ipca",
}


def _row_from_dict(data_referencia: str, d: IpcaDictRow) -> dict[str, object]:
    row: dict[str, object] = {"data_referencia": data_referencia.strip()[:10]}
    for src, dst in _DICT_TO_COL.items():
        if src in d:
            row[dst] = d[src]
    if "usa_fechado" in row:
        row["usa_fechado"] = int(bool(row["usa_fechado"]))
    return row


def to_dataframe(pairs: list[tuple[str, IpcaDictRow]]) -> pd.DataFrame:
    """Convert (date, dict) pairs to a sorted SQL-ready DataFrame."""
    if not pairs:
        return _EMPTY.copy()

    records = [_row_from_dict(date, d) for date, d in pairs]
    out = pd.DataFrame(records)
    for col in IPCA_DICT_COLUMNS:
        if col not in out.columns:
            out[col] = pd.NA
    out = out[list(IPCA_DICT_COLUMNS)]
    out = out.drop_duplicates(subset=["data_referencia"]).sort_values("data_referencia")
    return out.reset_index(drop=True)
