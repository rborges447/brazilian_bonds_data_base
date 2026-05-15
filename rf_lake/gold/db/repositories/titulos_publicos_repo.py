import sqlite3
from typing import Optional, Tuple

class TitulosPublicosRepo:
    @staticmethod
    def exists(conn: sqlite3.Connection, tipo_titulo: str, data_vencimento: str) -> bool:
        row = conn.execute("""
            SELECT 1
            FROM TITULOS_PUBLICOS
            WHERE tipo_titulo = ? AND data_vencimento = ?
        """, (tipo_titulo, data_vencimento)).fetchone()
        return row is not None

    @staticmethod
    def get_or_create(conn: sqlite3.Connection, tipo_titulo: str, data_vencimento: str,
                      expressao=None, data_base=None, codigo_selic=None, codigo_isin=None,
                      status: str = "ATIVO") -> Tuple[str, str]:
        """
        Insere o título público se não existir e, se já existir, preenche campos
        faltantes (NULL) com os valores informados (sem sobrescrever valores existentes).

        Motivação: muitos pipelines criam TITULOS_PUBLICOS apenas com a PK
        (tipo_titulo, data_vencimento). Em execuções futuras, quando uma fonte trouxer
        `expressao/codigo_selic/codigo_isin`, queremos completar o cadastro.
        """
        conn.execute(
            """
            INSERT INTO TITULOS_PUBLICOS (
                tipo_titulo,
                data_vencimento,
                expressao,
                data_base,
                codigo_selic,
                codigo_isin,
                status
            ) VALUES (
                ?,
                ?,
                NULLIF(?, ''),
                NULLIF(?, ''),
                NULLIF(?, ''),
                NULLIF(?, ''),
                ?
            )
            ON CONFLICT(tipo_titulo, data_vencimento)
            DO UPDATE SET
                expressao = COALESCE(excluded.expressao, TITULOS_PUBLICOS.expressao),
                data_base = COALESCE(excluded.data_base, TITULOS_PUBLICOS.data_base),
                codigo_selic = COALESCE(excluded.codigo_selic, TITULOS_PUBLICOS.codigo_selic),
                codigo_isin = COALESCE(excluded.codigo_isin, TITULOS_PUBLICOS.codigo_isin),
                status = CASE
                    WHEN excluded.status IS NOT NULL AND excluded.status != 'ATIVO'
                        THEN excluded.status
                    ELSE TITULOS_PUBLICOS.status
                END
            """,
            (
                tipo_titulo,
                data_vencimento,
                expressao,
                data_base,
                codigo_selic,
                codigo_isin,
                status,
            ),
        )
        return (tipo_titulo, data_vencimento)

    @staticmethod
    def get_by_pk(conn: sqlite3.Connection, tipo_titulo: str, data_vencimento: str) -> Optional[tuple]:
        return conn.execute("""
            SELECT tipo_titulo, data_vencimento, expressao, data_base, codigo_selic, codigo_isin, status
            FROM TITULOS_PUBLICOS
            WHERE tipo_titulo = ? AND data_vencimento = ?
        """, (tipo_titulo, data_vencimento)).fetchone()
