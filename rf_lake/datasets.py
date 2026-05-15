"""Registro de datasets e resolução de tarefas para jobs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

from rf_lake.incremental import missing_dates_gold
from rf_lake.settings import DATA_START_DATE

DateMode = Literal["missing_dates", "run_always"]


@dataclass(frozen=True)
class DatasetConfig:
    name: str
    date_mode: DateMode
    table: str | None = None
    date_col: str | None = None
    start_if_empty: str = DATA_START_DATE


@dataclass
class DatasetTask:
    name: str
    dates: list[str] = field(default_factory=list)
    config: DatasetConfig | None = None


DATASETS: dict[str, DatasetConfig] = {
    "mercado_secundario": DatasetConfig(
        name="mercado_secundario",
        date_mode="missing_dates",
        table="MERCADO_SECUNDARIO",
        date_col="data_referencia",
    ),
    "liquidacoes_mercado": DatasetConfig(
        name="liquidacoes_mercado",
        date_mode="missing_dates",
        table="LIQUIDACOES_MERCADO",
        date_col="data_referencia",
    ),
    "ajustes_bmf": DatasetConfig(
        name="ajustes_bmf",
        date_mode="missing_dates",
        table="AJUSTES_BMF",
        date_col="data_referencia",
    ),
    "leiloes": DatasetConfig(
        name="leiloes",
        date_mode="missing_dates",
        table="LEILOES",
        date_col="data_referencia",
    ),
    "ipca_indice": DatasetConfig(
        name="ipca_indice",
        date_mode="run_always",
    ),
    "projecoes": DatasetConfig(
        name="projecoes",
        date_mode="run_always",
    ),
    "feriados": DatasetConfig(
        name="feriados",
        date_mode="run_always",
    ),
}


def get_dataset_config(name: str) -> DatasetConfig:
    cfg = DATASETS.get(name)
    if cfg is None:
        raise ValueError(f"Dataset desconhecido: {name}")
    return cfg


def resolve_tasks(target_date: str | None = None) -> list[DatasetTask]:
    """
    Monta tarefas com datas candidatas (Gold).
    Cada fase Bronze/Silver/Gold aplica seu próprio filtro incremental.
    """
    if target_date is None:
        target_date = date.today().isoformat()

    tasks: list[DatasetTask] = []
    for cfg in DATASETS.values():
        if cfg.date_mode == "missing_dates":
            dates = missing_dates_gold(cfg, target_date)
        else:
            dates = [target_date] if cfg.name in ("projecoes",) else []

        tasks.append(DatasetTask(name=cfg.name, dates=dates, config=cfg))

    return tasks
