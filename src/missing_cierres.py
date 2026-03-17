"""
Script para identificar y procesar cierres faltantes
Busca en geocom.totals y cruza contra DW.cierres
"""
import pandas as pd
import sqlalchemy as sa
from src.config import DB_URL_DW, DB_URL_GEOCOM
from datetime import datetime


class MissingCierresProcessor:
    def __init__(self):
        self.eng_geocom = sa.create_engine(DB_URL_GEOCOM, fast_executemany=True)
        self.eng_dw = sa.create_engine(DB_URL_DW, fast_executemany=True)

    def get_totals_from_geocom(self, fecha_ini, fecha_fin):
        """
        Obtiene todos los cierres de la tabla totals en geocom
        fecha_ini y fecha_fin en formato YYYYMMDD
        Query basada en main.py procesar_cierres()
        """
        query = f"""
        SELECT
            RIGHT(CAST(YEAR(curr.closed) AS VARCHAR), 2) +
            RIGHT('0' + CAST(MONTH(curr.closed) AS VARCHAR), 2) +
            RIGHT('0' + CAST(DAY(curr.closed) AS VARCHAR), 2) +
            RIGHT('0' + CAST(DATEPART(HOUR, curr.closed) AS VARCHAR), 2) +
            RIGHT('0' + CAST(DATEPART(MINUTE, curr.closed) AS VARCHAR), 2) +
            RIGHT('0' + CAST(DATEPART(SECOND, curr.closed) AS VARCHAR), 2) +
            CAST(curr.localid AS VARCHAR) +
            CAST(curr.pos AS VARCHAR) AS id,
            curr.localid,
            curr.pos,
            curr.opened,
            curr.closed,
            COALESCE(prev.ticketsequencenumber, 0) AS ticketnumber_opened,
            COALESCE(curr.ticketsequencenumber, 0) AS ticketnumber_closed,
            curr.znumber
        FROM totals curr
        LEFT JOIN totals prev
            ON curr.localid = prev.localid
            AND curr.pos = prev.pos
            AND prev.subclass = 'postotal'
            AND prev.opened = (
                SELECT MAX(opened)
                FROM totals
                WHERE localid = curr.localid
                AND pos = curr.pos
                AND subclass = 'postotal'
                AND opened < curr.opened
            )
        WHERE curr.subclass = 'postotal'
        AND CAST(CONVERT(VARCHAR, curr.closed, 112) AS INT) BETWEEN {fecha_ini} AND {fecha_fin}
        AND curr.localid BETWEEN 100 AND 999
        ORDER BY curr.localid, curr.pos, curr.opened
        """
        try:
            df = pd.read_sql_query(query, self.eng_geocom)
            return df
        except Exception as e:
            print(f"Error al consultar totals de geocom: {e}")
            return pd.DataFrame()

    def get_cierres_from_dw(self, fecha_ini, fecha_fin):
        """
        Obtiene todos los cierres cargados en DW
        fecha_ini y fecha_fin en formato YYYYMMDD
        """
        query = f"""
        SELECT DISTINCT
            id,
            localid,
            pos,
            opened,
            closed
        FROM modelo_ventas_rauco.cierres
        WHERE CAST(CONVERT(VARCHAR, closed, 112) AS INT) BETWEEN {fecha_ini} AND {fecha_fin}
        ORDER BY localid, pos, closed
        """
        try:
            df = pd.read_sql_query(query, self.eng_dw)
            return df
        except Exception as e:
            print(f"Error al consultar cierres de DW: {e}")
            return pd.DataFrame()

    def find_missing_cierres(self, fecha_ini, fecha_fin):
        """
        Compara geocom.totals con DW.cierres y retorna los faltantes
        Criterio de cruce: ID (que incluye YYYYMMDDHHMMSS + localid + pos)
        ID es único porque contiene el timestamp completo del closed
        Por lo tanto la búsqueda es efectivamente por (localid + pos + z + closed)
        """
        df_geocom = self.get_totals_from_geocom(fecha_ini, fecha_fin)
        df_dw = self.get_cierres_from_dw(fecha_ini, fecha_fin)

        if df_geocom.empty:
            print(f"[ADVERTENCIA] No hay cierres en geocom para el período {fecha_ini}-{fecha_fin}")
            return pd.DataFrame()

        print(f"\n[RESUMEN] DEL PERÍODO {fecha_ini}-{fecha_fin}:")
        print(f"   - Cierres en geocom.totals: {len(df_geocom)}")
        print(f"   - Cierres en DW.cierres: {len(df_dw)}")

        if df_dw.empty:
            print(f"   - Cierres faltantes: {len(df_geocom)}")
            return df_geocom.copy()

        # Cruce por ID (que es único porque incluye timestamp completo: YYYYMMDDHHMMSS + localid + pos)
        # Esto garantiza búsqueda por (localid + pos + z + closed) implícitamente
        df_geocom_missing = df_geocom[~df_geocom['id'].isin(df_dw['id'])]

        print(f"   - Cierres faltantes: {len(df_geocom_missing)}")

        return df_geocom_missing[['id', 'localid', 'pos', 'opened', 'closed', 'ticketnumber_opened', 'ticketnumber_closed', 'znumber']]

    def validate_closure_data(self, localid, pos, closed_fmt):
        """
        Valida que un cierre exista en geocom y tenga datos válidos
        closed_fmt en formato YYYYMMDD
        """
        query = f"""
        SELECT
            RIGHT(CAST(YEAR(curr.closed) AS VARCHAR), 2) +
            RIGHT('0' + CAST(MONTH(curr.closed) AS VARCHAR), 2) +
            RIGHT('0' + CAST(DAY(curr.closed) AS VARCHAR), 2) +
            RIGHT('0' + CAST(DATEPART(HOUR, curr.closed) AS VARCHAR), 2) +
            RIGHT('0' + CAST(DATEPART(MINUTE, curr.closed) AS VARCHAR), 2) +
            RIGHT('0' + CAST(DATEPART(SECOND, curr.closed) AS VARCHAR), 2) +
            CAST(curr.localid AS VARCHAR) +
            CAST(curr.pos AS VARCHAR) AS id,
            curr.localid,
            curr.pos,
            curr.opened,
            curr.closed,
            COALESCE(prev.ticketsequencenumber, 0) AS ticketnumber_opened,
            COALESCE(curr.ticketsequencenumber, 0) AS ticketnumber_closed,
            curr.znumber
        FROM totals curr
        LEFT JOIN totals prev
            ON curr.localid = prev.localid
            AND curr.pos = prev.pos
            AND prev.subclass = 'postotal'
            AND prev.opened = (
                SELECT MAX(opened)
                FROM totals
                WHERE localid = curr.localid
                AND pos = curr.pos
                AND subclass = 'postotal'
                AND opened < curr.opened
            )
        WHERE curr.subclass = 'postotal'
        AND curr.localid = {localid}
        AND curr.pos = {pos}
        AND CAST(CONVERT(VARCHAR, curr.closed, 112) AS INT) = {closed_fmt}
        """
        try:
            df = pd.read_sql_query(query, self.eng_geocom)
            return df if not df.empty else None
        except Exception as e:
            print(f"Error validando cierre {localid}-{pos}-{closed_fmt}: {e}")
            return None


def print_missing_summary(df_missing):
    """
    Imprime un resumen formateado de los cierres faltantes
    """
    if df_missing.empty:
        print("[OK] Todos los cierres han sido cargados en DW")
        return

    print("\n" + "="*80)
    print("CIERRES FALTANTES EN DW")
    print("="*80)

    # Agrupar por local
    for localid in sorted(df_missing['localid'].unique()):
        df_local = df_missing[df_missing['localid'] == localid]
        print(f"\nLocal {localid}:")

        # Agrupar por POS dentro del local
        for pos in sorted(df_local['pos'].unique()):
            df_pos = df_local[df_local['pos'] == pos]
            print(f"  POS {pos}: {len(df_pos)} cierre(s) faltante(s)")

            for _, row in df_pos.iterrows():
                print(f"    - Closed: {row['closed']} | ID: {row['id']} | Z: {row['znumber']}")

    print("\n" + "="*80)
    print(f"Total de cierres faltantes: {len(df_missing)}")
    print("="*80 + "\n")
