#!/usr/bin/env python3
"""
Análisis de anomalías en cierres:
- Identifica cierres con Z anomalamente cercanos (ej: Z170, Z171 en pocas horas)
- Valida si tienen datos reales en geocom
- Marca cuáles pueden procesarse con seguridad y cuáles necesitan limpieza
"""

import pandas as pd
from datetime import datetime, timedelta
import sqlalchemy as sa
from src.config import DB_URL_GEOCOM, DB_URL_DW

class AnomalyAnalyzer:
    def __init__(self):
        self.eng_geocom = sa.create_engine(DB_URL_GEOCOM)
        self.eng_dw = sa.create_engine(DB_URL_DW)

    def get_z_sequence_for_local(self, localid, pos, fecha_ini, fecha_fin):
        """Obtiene la secuencia de Z en orden para un local/pos en un período"""
        query = f"""
        SELECT
            localid,
            pos,
            znumber,
            closed,
            ticketsequencenumber
        FROM totals
        WHERE subclass = 'postotal'
        AND localid = {localid}
        AND pos = {pos}
        AND CAST(CONVERT(VARCHAR, closed, 112) AS INT) BETWEEN {fecha_ini} AND {fecha_fin}
        ORDER BY closed
        """
        df = pd.read_sql(query, self.eng_geocom)

        # Calcular minutos desde cierre anterior en Python
        if len(df) > 0:
            df['minutes_from_previous'] = df['closed'].diff().dt.total_seconds() / 60

        return df

    def identify_close_z_pairs(self, df_sequence):
        """Identifica pares de Z muy cercanos en tiempo (< 5 minutos)"""
        anomalies = []
        for idx in range(len(df_sequence) - 1):
            row = df_sequence.iloc[idx]
            next_row = df_sequence.iloc[idx + 1]

            minutes_diff = row['minutes_from_previous']
            z_diff = next_row['znumber'] - row['znumber']

            # Si hay muy poco tiempo entre cierres, es sospechoso
            if minutes_diff is not None and minutes_diff < 5:
                anomalies.append({
                    'localid': row['localid'],
                    'pos': row['pos'],
                    'z_num': int(row['znumber']),
                    'z_next': int(next_row['znumber']),
                    'z_diff': z_diff,
                    'closed': row['closed'],
                    'closed_next': next_row['closed'],
                    'minutes_diff': int(minutes_diff),
                    'anomaly_type': 'CLOSE_Z_PAIRS' if z_diff == 1 else 'SKIP_Z_SEQUENCE'
                })

        return anomalies

    def check_data_validity(self, localid, pos, closed_str):
        """Verifica si un cierre tiene datos reales en geocom"""
        opened_str = (datetime.strptime(closed_str, '%Y%m%d') - timedelta(days=1)).strftime('%Y%m%d')

        # Contar ventas
        query_ventas = f"""
        SELECT COUNT(*) as count_ventas
        FROM tickets
        WHERE localid = {localid}
        AND pos = {pos}
        AND documenttype = 'sale'
        AND CAST(CONVERT(VARCHAR, opendate, 112) AS INT) BETWEEN {opened_str} AND {closed_str}
        """
        count_ventas = pd.read_sql(query_ventas, self.eng_geocom).iloc[0]['count_ventas']

        # Contar pagos
        query_pagos = f"""
        SELECT COUNT(*) as count_pagos
        FROM tickets t
        INNER JOIN payments p ON t.opendate = p.opendate AND t.localid = p.localid
            AND t.ticketnumber = p.ticketnumber AND t.pos = p.pos
        INNER JOIN paymentmodes pm ON p.paymentmode = pm.id
        WHERE t.localid = {localid}
        AND t.pos = {pos}
        AND t.documenttype = 'sale'
        AND pm.id NOT IN (40)
        AND CAST(CONVERT(VARCHAR, t.opendate, 112) AS INT) BETWEEN {opened_str} AND {closed_str}
        """
        count_pagos = pd.read_sql(query_pagos, self.eng_geocom).iloc[0]['count_pagos']

        return {
            'has_sales': count_ventas > 0,
            'has_payments': count_pagos > 0,
            'total_sales': count_ventas,
            'total_payments': count_pagos,
            'data_quality': 'VALID' if (count_ventas > 0 and count_pagos > 0) else 'SUSPICIOUS'
        }

    def check_orphan_details_in_dw(self, localid, pos, closed_str):
        """Verifica si hay detalles huérfanos en DW sin cabecera"""
        query = f"""
        SELECT COUNT(*) as count_details
        FROM DW.dbo.cierres_detalle
        WHERE localid = {localid}
        AND pos = {pos}
        AND CAST(CONVERT(VARCHAR, closed, 112) AS INT) = {closed_str.replace('-', '')}
        """
        try:
            count = pd.read_sql(query, self.eng_dw).iloc[0]['count_details']
            return count
        except:
            return 0

    def generate_report(self, problematic_cases):
        """Genera reporte de anomalías y recomendaciones"""

        print("\n" + "="*80)
        print("ANÁLISIS DE ANOMALÍAS EN CIERRES FALTANTES")
        print("="*80)

        report = []

        for case in problematic_cases:
            localid = case[0]
            pos = case[1]
            closed = case[2]

            print(f"\n[CASO] Local {localid} | POS {pos} | Closed {closed}")
            print("-" * 40)

            # Obtener secuencia Z
            fecha_ini = str(int(closed) - 10)
            fecha_fin = str(int(closed) + 10)
            df_sequence = self.get_z_sequence_for_local(localid, pos, fecha_ini, fecha_fin)

            print(f"Secuencia Z encontrada:")
            print(df_sequence[['znumber', 'closed', 'minutes_from_previous']].to_string())

            # Identificar anomalías
            anomalies = self.identify_close_z_pairs(df_sequence)

            if anomalies:
                print(f"\n[!] ANOMALIAS DETECTADAS:")
                for anom in anomalies:
                    print(f"  - Z{anom['z_num']} -> Z{anom['z_next']} en {anom['minutes_diff']} minutos ({anom['anomaly_type']})")

            # Validar datos
            data_check = self.check_data_validity(localid, pos, closed)
            print(f"\n[*] Validacion de datos:")
            print(f"  - Ventas: {data_check['total_sales']} tickets")
            print(f"  - Pagos: {data_check['total_payments']}")
            print(f"  - Calidad: {data_check['data_quality']}")

            # Verificar detalles huérfanos
            orphans = self.check_orphan_details_in_dw(localid, pos, closed)
            print(f"\n[*] Detalles en DW: {orphans} registros")

            # Recomendación
            recommendation = self._get_recommendation(anomalies, data_check, orphans)
            print(f"\n[OK] RECOMENDACION: {recommendation}")

            report.append({
                'localid': localid,
                'pos': pos,
                'closed': closed,
                'has_anomaly': len(anomalies) > 0,
                'data_valid': data_check['data_quality'] == 'VALID',
                'orphans_count': orphans,
                'recommendation': recommendation
            })

        return pd.DataFrame(report)

    def _get_recommendation(self, anomalies, data_check, orphans):
        """Determina recomendacion segun anomalias y datos"""

        if data_check['data_quality'] == 'SUSPICIOUS':
            return "[SKIP] No tiene datos reales / Z anomalamente cercano"

        if orphans > 0:
            return "[CLEAN] Eliminar detalles hurfanos antes de cargar"

        if len(anomalies) > 0:
            return "[CHECK] Z muy cercanos, pero tiene datos validos"

        return "[LOAD] Carga normal sin problemas"


if __name__ == "__main__":
    analyzer = AnomalyAnalyzer()

    # Casos con FAILs: Local, POS, Closed (YYYYMMDD)
    problematic_cases = [
        (286, 1, '20260112'),
        (286, 1, '20260122'),
        (322, 1, '20260122'),
        (817, 1, '20260131'),
    ]

    report = analyzer.generate_report(problematic_cases)

    # Guardar reporte
    report.to_csv('anomaly_report.csv', index=False)
    print("\n" + "="*80)
    print(f"[OK] Reporte guardado en: anomaly_report.csv")
    print("="*80)
