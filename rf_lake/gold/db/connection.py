"""
Gerenciamento de conexões SQLite.

Fornece funções para criar e gerenciar conexões com o banco de dados SQLite.
Configurado para suportar múltiplos acessos simultâneos (WAL mode).
"""
import sqlite3
from pathlib import Path
from typing import Optional, Union

from rf_lake.settings import DB_PATH


def get_conn(db_path: Optional[Union[str, Path]] = None) -> sqlite3.Connection:
    """
    Cria uma nova conexão com o banco de dados SQLite.
    
    Configurações aplicadas:
    - Foreign keys habilitadas
    - WAL mode (Write-Ahead Logging) para suportar múltiplos leitores simultâneos
    - Synchronous mode NORMAL para melhor performance
    - Timeout de 30 segundos para operações de lock
    
    Args:
        db_path: Caminho opcional para o arquivo do banco de dados.
                 Se não fornecido, usa o caminho padrão configurado.
                 Pode ser string ou Path.
    
    Returns:
        Conexão SQLite configurada.
    
    Note:
        A conexão retornada deve ser fechada explicitamente ou usada
        em um context manager. Para uso automático, use Database.transaction().
    """
    path = db_path or DB_PATH
    if isinstance(path, str):
        path = Path(path)
    
    # Garante que o diretório existe
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Cria conexão com timeout para operações de lock
    conn = sqlite3.connect(str(path), timeout=30)
    
    # Configurações para suportar múltiplos acessos simultâneos
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    
    return conn
