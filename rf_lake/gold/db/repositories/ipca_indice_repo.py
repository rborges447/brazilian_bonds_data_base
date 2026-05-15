import sqlite3
from typing import List, Optional, Tuple


class IpcaIndiceRepo:
    @staticmethod
    def upsert(
        conn: sqlite3.Connection,
        *,
        ref_month: str,
        ipca_index: float | None,
        ipca_mom: float | None,
    ) -> None:
        conn.execute(
            """
            INSERT INTO IPCA_INDICE (ref_month, ipca_index, ipca_mom)
            VALUES (?, ?, ?)
            ON CONFLICT(ref_month)
            DO UPDATE SET
                ipca_index = excluded.ipca_index,
                ipca_mom = excluded.ipca_mom
            """,
            (ref_month, ipca_index, ipca_mom),
        )

    @staticmethod
    def get_max_ref_month(conn: sqlite3.Connection) -> str | None:
        row = conn.execute("SELECT MAX(ref_month) FROM IPCA_INDICE;").fetchone()
        if not row or not row[0]:
            return None
        return str(row[0])

    @staticmethod
    def get_last_months(
        conn: sqlite3.Connection,
        months: int,
    ) -> List[Tuple[str, Optional[float], Optional[float]]]:
        """
        Retorna os últimos `months` registros de IPCA_INDICE.

        Args:
            months: quantidade de meses a retornar (deve ser >= 1)

        Returns:
            Lista de tuplas (ref_month, ipca_index, ipca_mom) em ordem ascendente de ref_month.
        """
        if months <= 0:
            return []

        rows = conn.execute(
            """
            SELECT ref_month, ipca_index, ipca_mom
            FROM (
                SELECT ref_month, ipca_index, ipca_mom
                FROM IPCA_INDICE
                ORDER BY ref_month DESC
                LIMIT ?
            )
            ORDER BY ref_month ASC
            """,
            (int(months),),
        ).fetchall()

        return [(str(r[0]), r[1], r[2]) for r in rows]

