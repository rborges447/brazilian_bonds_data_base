"""Executa um único dataset nas três camadas (debug)."""

from __future__ import annotations

from rf_lake.bootstrap import bootstrap
from rf_lake.datasets import get_dataset_config
from rf_lake.logging import get_logger, setup_logging
from rf_lake.pipeline import run_dataset

setup_logging()
logger = get_logger(__name__)

PIPELINE_NAMES = (
    "mercado_secundario",
    "liquidacoes_mercado",
    "ajustes_bmf",
    "feriados",
    "leiloes",
    "ipca_indice",
    "projecoes",
)


def run_one(pipeline: str, date: str) -> dict:
    bootstrap()

    if pipeline not in PIPELINE_NAMES:
        raise ValueError(f"Pipeline desconhecido: {pipeline}. Opções: {list(PIPELINE_NAMES)}")

    cfg = get_dataset_config(pipeline)
    if pipeline == "feriados":
        dates: list[str] = []
    elif cfg.date_mode == "run_always" and pipeline == "ipca_indice":
        dates = []
    else:
        dates = [date]

    logger.info("run_one %s dates=%s", pipeline, dates or "snapshot")
    result = run_dataset(pipeline, dates, end_date=date)
    return {
        "pipeline": pipeline,
        "date": date,
        "status": "success" if result.get("persisted") else "failed",
        **result,
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Uso: python -m rf_lake.jobs.run_one PIPELINE DATE")
        sys.exit(1)
    print(run_one(sys.argv[1], sys.argv[2]))
