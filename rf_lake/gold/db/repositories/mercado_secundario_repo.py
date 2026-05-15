import sqlite3

class MercadoSecundarioRepo:
    @staticmethod
    def upsert(conn: sqlite3.Connection,
               tipo_titulo: str,
               data_vencimento: str,
               data_referencia: str,
               taxa_anbima=None,
               intervalo_min_d0=None, intervalo_max_d0=None,
               intervalo_min_d1=None, intervalo_max_d1=None,
               pu=None) -> None:
               
        conn.execute("""
            INSERT INTO MERCADO_SECUNDARIO (
            tipo_titulo, data_vencimento, data_referencia,
            taxa_anbima, intervalo_min_d0, intervalo_max_d0,
            intervalo_min_d1, intervalo_max_d1,
            pu
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(tipo_titulo, data_vencimento, data_referencia)
            DO UPDATE SET
            taxa_anbima = excluded.taxa_anbima,
            intervalo_min_d0 = excluded.intervalo_min_d0,
            intervalo_max_d0 = excluded.intervalo_max_d0,
            intervalo_min_d1 = excluded.intervalo_min_d1,
            intervalo_max_d1 = excluded.intervalo_max_d1,
            pu = excluded.pu
        """, (tipo_titulo, data_vencimento, data_referencia, taxa_anbima,
            intervalo_min_d0, intervalo_max_d0,
            intervalo_min_d1, intervalo_max_d1,
            pu))
