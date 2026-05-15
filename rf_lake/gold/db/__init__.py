"""
Módulo de banco de dados SQLite: persistência e leitura de dados.

Este módulo contém toda a infraestrutura de banco de dados:
- Conexões SQLite (WAL mode, foreign keys)
- Sistema de migrações versionadas
- Repositórios (CRUD por tabela)
- Queries de leitura (get_*)
- Schema e metadados

Responsabilidades:
- Gerenciar conexões com SQLite
- Executar migrações de schema
- Fornecer interfaces para persistência (repositories) e leitura (queries)
- Manter metadados de schema (colunas, tipos, rename maps)

Dependências permitidas:
- settings (para DB_PATH, MIGRATIONS_DIR)
- logging (para logs)
- Bibliotecas padrão e terceiros (sqlite3, pandas, pathlib)

Dependências proibidas:
- sources/ (não deve conhecer fontes externas)
- etl/ (não deve conhecer pipelines)
- jobs/ (não deve conhecer orquestração)
- export/ (não deve conhecer exportação)
- data_reader/ (não deve conhecer leitor de dados de produto)
"""

from rf_lake.gold.db import schema
from rf_lake.gold.db.connection import get_conn
from rf_lake.gold.db.migrate import apply_migrations

__all__ = ["apply_migrations", "get_conn", "schema"]
