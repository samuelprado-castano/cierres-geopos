#!/usr/bin/env python3
"""
Limpieza de detalles hurfanos en DW
Elimina registros de detalle cuando existe un cierre parcial (detalles sin cabecera)
para asegurar DELETE+INSERT cuando se recargan los cierres.

Uso:
    python cleanup_orphan_details.py <localid> <pos> <closed_yyyymmdd>

Ejemplo:
    python cleanup_orphan_details.py 286 1 20260112
    python cleanup_orphan_details.py 817 1 20260131
"""

import sys
import pandas as pd
import sqlalchemy as sa
from datetime import datetime
from src.config import DB_URL_DW

class OrphanDetailsCleaner:
    def __init__(self):
        self.eng_dw = sa.create_engine(DB_URL_DW)

    def get_closure_id(self, localid, pos, closed_yyyymmdd):
        """
        Obtiene el ID del cierre en formato que usa DW:
        YYYYMMDDHHMMSST + localid + pos

        Necesita buscar en los detalles existentes porque el ID se calcula de la hora exacta
        """
        query = f"""
        SELECT DISTINCT id
        FROM modelo_ventas_rauco.dbo.cierres_detalle
        WHERE localid = {localid}
        AND pos = {pos}
        AND CAST(CONVERT(VARCHAR, closed, 112) AS INT) = {closed_yyyymmdd}
        """
        try:
            result = pd.read_sql(query, self.eng_dw)
            if len(result) > 0:
                return result.iloc[0]['id']
            return None
        except Exception as e:
            print(f"[ERROR] Error obteniendo ID del cierre: {e}")
            return None

    def count_orphan_records(self, localid, pos, closed_yyyymmdd):
        """Cuenta registros hurfanos en todas las tablas de detalle"""
        counts = {}

        tables = [
            ('cierres_detalle', 'modelo_ventas_rauco'),
            ('cierres_precio_producto', 'modelo_ventas_rauco'),
            ('cierres_medio_pago', 'modelo_ventas_rauco'),
            ('cierres_depositos', 'modelo_ventas_rauco'),
            ('cierres_guias_detalle', 'modelo_ventas_rauco'),
        ]

        for table, schema in tables:
            query = f"""
            SELECT COUNT(*) as count
            FROM {schema}.dbo.{table}
            WHERE localid = {localid}
            AND pos = {pos}
            AND CAST(CONVERT(VARCHAR, closed, 112) AS INT) = {closed_yyyymmdd}
            """
            try:
                result = pd.read_sql(query, self.eng_dw)
                counts[table] = result.iloc[0]['count']
            except:
                counts[table] = 0

        return counts

    def delete_orphan_details(self, localid, pos, closed_yyyymmdd, dry_run=False):
        """
        Elimina todos los detalles hurfanos para un cierre especifico

        Args:
            localid: ID del local
            pos: Numero de caja
            closed_yyyymmdd: Fecha de cierre en formato YYYYMMDD
            dry_run: Si True, solo reporta sin eliminar
        """
        print(f"\n{'='*70}")
        print(f"LIMPIEZA DE DETALLES HURFANOS")
        print(f"{'='*70}")
        print(f"Local: {localid} | POS: {pos} | Closed: {closed_yyyymmdd}")

        # Contar registros antes
        counts_before = self.count_orphan_records(localid, pos, closed_yyyymmdd)
        total_before = sum(counts_before.values())

        print(f"\n[*] Registros encontrados ANTES:")
        for table, count in counts_before.items():
            if count > 0:
                print(f"  - {table}: {count}")

        if total_before == 0:
            print(f"\n[OK] No hay detalles hurfanos. Nada que limpiar.")
            return {'status': 'OK', 'deleted': 0}

        if dry_run:
            print(f"\n[*] DRY RUN MODE - No se eliminara nada")
            return {'status': 'DRY_RUN', 'would_delete': total_before}

        # Proceder con la eliminacion
        print(f"\n[*] Eliminando {total_before} registros...")

        try:
            tables_to_delete = [
                ('cierres_detalle', 'modelo_ventas_rauco'),
                ('cierres_precio_producto', 'modelo_ventas_rauco'),
                ('cierres_medio_pago', 'modelo_ventas_rauco'),
                ('cierres_depositos', 'modelo_ventas_rauco'),
                ('cierres_guias_detalle', 'modelo_ventas_rauco'),
            ]

            with self.eng_dw.begin() as conn:
                for table, schema in tables_to_delete:
                    delete_query = f"""
                    DELETE FROM {schema}.dbo.{table}
                    WHERE localid = {localid}
                    AND pos = {pos}
                    AND CAST(CONVERT(VARCHAR, closed, 112) AS INT) = {closed_yyyymmdd}
                    """
                    conn.execute(sa.text(delete_query))

            # Verificar que se eliminaron
            counts_after = self.count_orphan_records(localid, pos, closed_yyyymmdd)
            total_after = sum(counts_after.values())

            print(f"\n[OK] Eliminacion completada:")
            print(f"  - Antes: {total_before} registros")
            print(f"  - Despues: {total_after} registros")
            print(f"  - Eliminados: {total_before - total_after}")

            return {
                'status': 'SUCCESS',
                'deleted': total_before - total_after,
                'details': counts_before
            }

        except Exception as e:
            print(f"\n[ERROR] Error durante eliminacion: {e}")
            return {'status': 'ERROR', 'error': str(e)}

    def cleanup_all_problematic(self):
        """Limpia todos los cierres con FAILs conocidos"""
        problematic_cases = [
            (286, 1, '20260112'),
            (286, 1, '20260122'),
            (322, 1, '20260122'),
            (817, 1, '20260131'),
        ]

        results = []
        for localid, pos, closed_yyyymmdd in problematic_cases:
            result = self.delete_orphan_details(localid, pos, closed_yyyymmdd)
            results.append({
                'localid': localid,
                'pos': pos,
                'closed': closed_yyyymmdd,
                **result
            })

        # Resumen final
        print(f"\n{'='*70}")
        print(f"RESUMEN DE LIMPIEZA")
        print(f"{'='*70}")
        total_deleted = sum(r.get('deleted', 0) for r in results)
        print(f"[OK] Total registros eliminados: {total_deleted}")

        return pd.DataFrame(results)


def main():
    if len(sys.argv) < 2:
        # Sin argumentos: limpiar todos los casos problematicos
        print("Usando caso por defecto: LIMPIAR TODOS LOS FAILs CONOCIDOS\n")
        cleaner = OrphanDetailsCleaner()
        result_df = cleaner.cleanup_all_problematic()
        result_df.to_csv('cleanup_results.csv', index=False)
        print(f"\n[OK] Resultados guardados en: cleanup_results.csv")

    elif len(sys.argv) == 4:
        # Con argumentos especificos
        localid = int(sys.argv[1])
        pos = int(sys.argv[2])
        closed_yyyymmdd = sys.argv[3]

        cleaner = OrphanDetailsCleaner()
        result = cleaner.delete_orphan_details(localid, pos, closed_yyyymmdd)

        if result['status'] == 'SUCCESS':
            print(f"\n[OK] Limpieza completada exitosamente")
            sys.exit(0)
        else:
            print(f"\n[ERROR] Error en limpieza")
            sys.exit(1)
    else:
        print(f"Uso:")
        print(f"  python cleanup_orphan_details.py                    # Limpiar todos los FAILs")
        print(f"  python cleanup_orphan_details.py <localid> <pos> <YYYYMMDD>  # Limpiar especifico")
        sys.exit(1)


if __name__ == "__main__":
    main()
