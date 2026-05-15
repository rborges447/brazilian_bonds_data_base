"""Repositórios para operações CRUD no banco de dados."""

from rf_lake.gold.db.repositories.ajustes_bmf_repo import AjustesBmfRepo
from rf_lake.gold.db.repositories.contratos_bmf_repo import ContratosBmfRepo
from rf_lake.gold.db.repositories.feriados_repo import FeriadosRepo
from rf_lake.gold.db.repositories.ipca_indice_repo import IpcaIndiceRepo
from rf_lake.gold.db.repositories.leiloes_repo import LeiloesRepo
from rf_lake.gold.db.repositories.liquidacoes_mercado_repo import LiquidacoesMercadoRepo
from rf_lake.gold.db.repositories.mercado_secundario_repo import MercadoSecundarioRepo
from rf_lake.gold.db.repositories.projecoes_repo import ProjecoesRepo
from rf_lake.gold.db.repositories.titulos_publicos_repo import TitulosPublicosRepo

__all__ = [
    "AjustesBmfRepo",
    "ContratosBmfRepo",
    "FeriadosRepo",
    "IpcaIndiceRepo",
    "LeiloesRepo",
    "LiquidacoesMercadoRepo",
    "MercadoSecundarioRepo",
    "ProjecoesRepo",
    "TitulosPublicosRepo",
]
