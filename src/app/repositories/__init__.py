"""Gold table repositories (schema v2)."""

from app.repositories.base import Repository
from app.repositories.bmf import BmfRepository
from app.repositories.cdi import CdiRepository
from app.repositories.feriados import FeriadosRepository
from app.repositories.ipca_dict import IpcaDictRepository
from app.repositories.leiloes import LeiloesRepository
from app.repositories.liquidacoes_mercado import LiquidacoesMercadoRepository
from app.repositories.mercado_secundario import MercadoSecundarioRepository
from app.repositories.ptax import PtaxRepository
from app.repositories.titulos_publicos import TitulosPublicosRepository

__all__ = [
    "BmfRepository",
    "CdiRepository",
    "FeriadosRepository",
    "IpcaDictRepository",
    "LeiloesRepository",
    "LiquidacoesMercadoRepository",
    "MercadoSecundarioRepository",
    "PtaxRepository",
    "Repository",
    "TitulosPublicosRepository",
]
