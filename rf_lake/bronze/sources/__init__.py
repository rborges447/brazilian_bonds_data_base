"""
Módulo de fontes de dados externas: clientes HTTP para APIs externas.

Este módulo contém clientes para buscar dados brutos de fontes externas:
- ANBIMA (mercado secundário, projeções, leilões)
- BCB (liquidações de mercado)
- Tesouro Direto
- UpToData (ajustes BMF)
- Sidra/IBGE (IPCA)

Responsabilidades:
- Autenticação com APIs externas (quando necessário)
- Fetch de dados brutos (HTTP requests)
- Mapeamento básico de resposta API → DataFrame
- Validação de dados brutos

Dependências permitidas:
- settings (para credenciais, timeouts)
- logging (para logs)
- Bibliotecas padrão e terceiros (requests, pandas)

Dependências proibidas:
- db/ (não deve conhecer persistência)
- etl/ (não deve conhecer pipelines)
- jobs/ (não deve conhecer orquestração)
- export/ (não deve conhecer exportação)
"""

from rf_lake.bronze.sources.anbima.client import AnbimaClient

__all__ = ["AnbimaClient"]
