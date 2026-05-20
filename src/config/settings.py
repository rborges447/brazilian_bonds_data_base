"""Central configuration (Pydantic Settings per data source)."""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.paths import PROJECT_ROOT, resolve_path


def _validate_iso_date(value: str | date, name: str) -> date:
    if isinstance(value, date):
        return value
    text = str(value).strip()
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{name} is invalid (expected YYYY-MM-DD): {text!r}") from exc


class PathSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    data_root: Path = Path("data")
    sqlite_db_path: Path = Path("data/app.db")
    data_start_date: date = date(2026, 1, 1)

    @field_validator("data_start_date", mode="before")
    @classmethod
    def _parse_data_start_date(cls, value: object) -> date:
        return _validate_iso_date(value, "DATA_START_DATE")  # type: ignore[arg-type]


class AnbimaSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ANBIMA_", extra="ignore")

    client_id: str = ""
    client_secret: str = ""
    timeout: int = 30
    max_retries: int = 3
    token_url: str = "https://api.anbima.com.br/oauth/access-token"
    mercado_secundario_tpf_url: str = (
        "https://api.anbima.com.br/feed/precos-indices/v1/titulos-publicos/mercado-secundario-TPF"
    )
    vna_url: str = "https://api.anbima.com.br/feed/precos-indices/v1/titulos-publicos/vna"
    projecoes_url: str = (
        "https://api.anbima.com.br/feed/precos-indices/v1/titulos-publicos/projecoes"
    )
    estimativa_selic_url: str = (
        "https://api.anbima.com.br/feed/precos-indices/v1/titulos-publicos/estimativa-selic"
    )


class FeriadosSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FERIADOS_", extra="ignore")

    xls_url: str = "https://www.anbima.com.br/feriados/arqs/feriados_nacionais.xls"
    timeout: int = 30


class BcbSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BCB_", extra="ignore")

    base_url: str = "https://www4.bcb.gov.br/pom/demab/negociacoes/download"
    sgs_base_url: str = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"
    cdi_series_id: int = 11
    ptax_base_url: str = "https://ptax.bcb.gov.br/ptax_internet/consultaBoletim.do"
    ptax_moeda_code: int = 61
    timeout: int = 30
    max_retries: int = 3


class TesouroSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TESOURO_", extra="ignore")

    base_url: str = "https://apiapex.tesouro.gov.br/aria"
    resultados_path: str = "/v1/api-leiloes-pub/custom/resultados"
    timeout: int = 30
    max_retries: int = 3


class SidraSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SIDRA_", extra="ignore")

    max_retries: int = 3
    default_period: str = "last 60"
    table_code_ipca: str = "6691"
    var_ipca_index: str = "2266"
    var_ipca_mom: str = "63"
    territorial_level_br: str = "1"
    ibge_territorial_code_br: str = "1"


class UptodataSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="UPTODATA_", extra="ignore")

    pasta_interest_rate_base: str = ""
    arquivo_interest_rate_base: str = ""
    pasta_currency_base: str = ""
    arquivo_currency_base: str = "Currency_SettlementPriceFile_Futures_"


class AppSettings:
    """Aggregates per-source settings and resolved filesystem paths."""

    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = project_root or PROJECT_ROOT
        self.log_level: str = "INFO"
        self.paths = PathSettings()
        self.anbima = AnbimaSettings()
        self.feriados = FeriadosSettings()
        self.bcb = BcbSettings()
        self.tesouro = TesouroSettings()
        self.sidra = SidraSettings()
        self.uptodata = UptodataSettings()
        self._apply_log_level()

    def _apply_log_level(self) -> None:
        import logging
        import os

        level_name = os.getenv("LOG_LEVEL", self.log_level).strip().upper()
        self.log_level = level_name
        logging.basicConfig(
            level=getattr(logging, level_name, logging.INFO),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            force=False,
        )

    @property
    def data_root(self) -> Path:
        return resolve_path(self.paths.data_root, self.project_root)

    @property
    def bronze_root(self) -> Path:
        return self.data_root / "raw"

    @property
    def silver_root(self) -> Path:
        return self.data_root / "silver"

    @property
    def meta_dir(self) -> Path:
        return self.data_root / "meta"

    @property
    def db_path(self) -> Path:
        return resolve_path(self.paths.sqlite_db_path, self.project_root)

    @property
    def migrations_dir(self) -> Path:
        return self.project_root / "migrations"

    @property
    def data_start_date(self) -> date:
        return self.paths.data_start_date

    def ensure_data_layout(self) -> None:
        """Create data directories (raw, silver, meta, SQLite parent folder)."""
        for path in (self.data_root, self.bronze_root, self.silver_root, self.meta_dir, self.db_path.parent):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> AppSettings:
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    return AppSettings()
