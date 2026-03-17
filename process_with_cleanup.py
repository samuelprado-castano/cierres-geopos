#!/usr/bin/env python3
"""
Proceso completo de identificacion, analisis, limpieza y carga de cierres faltantes.

Pasos:
1. Identificar cierres faltantes (missing_cierres.py)
2. Ejecutar analisis de anomalias (analyze_anomalies.py)
3. Limpiar detalles hurfanos (cleanup_orphan_details.py)
4. Generar comandos de carga ajustados por Z
5. Crear reporte final

Uso:
    python process_with_cleanup.py
"""

import pandas as pd
import sqlalchemy as sa
from datetime import datetime, timedelta
from src.missing_cierres import MissingCierresProcessor
from cleanup_orphan_details import OrphanDetailsCleaner
from src.config import DB_URL_GEOCOM, DB_URL_DW

class CleanupAwareProcessor:
    def __init__(self):
        self.eng_geocom = sa.create_engine(DB_URL_GEOCOM)
        self.missing_processor = MissingCierresProcessor()
        self.cleaner = OrphanDetailsCleaner()

    def get_znumber_for_closure(self, localid, pos, closed_yyyymmdd):
        """
        Obtiene el Z (znumber) para un cierre especifico.
        El Z es mas preciso que closed porque es el numero secuencial de cierre.
        """
        query = f"""
        SELECT TOP 1
            znumber,
            closed,
            ticketsequencenumber
        FROM totals
        WHERE subclass = 'postotal'
        AND localid = {localid}
        AND pos = {pos}
        AND CAST(CONVERT(VARCHAR, closed, 112) AS INT) = {closed_yyyymmdd}
        ORDER BY closed DESC
        """
        try:
            result = pd.read_sql(query, self.eng_geocom)
            if len(result) > 0:
                return {
                    'znumber': int(result.iloc[0]['znumber']),
                    'closed': result.iloc[0]['closed'],
                    'ticketnumber': int(result.iloc[0]['ticketsequencenumber']) if result.iloc[0]['ticketsequencenumber'] else 0
                }
            return None
        except Exception as e:
            print(f"[ERROR] Error obteniendo Z para {localid}/{pos}/{closed_yyyymmdd}: {e}")
            return None

    def identify_anomalies_from_csv(self, csv_path='qa_missing_cierres.csv'):
        """Lee el CSV de QA y extrae los casos con FAIL"""
        df = pd.read_csv(csv_path)

        # Filtrar solo FAILs en la prueba de detalles
        fails = df[(df['test'] == 'Detalle del cierre NO existe en DW') & (df['status'] == '✗ FAIL')]

        # Agrupar por localid, pos, closed para evitar duplicados
        problematic = fails.drop_duplicates(subset=['localid', 'pos', 'closed'])

        print(f"\n[*] CASOS CON FAILs ENCONTRADOS: {len(problematic)}")
        print(f"{'='*70}")

        cases = []
        for idx, row in problematic.iterrows():
            localid = int(row['localid'])
            pos = int(row['pos'])
            closed_yyyymmdd = str(int(row['closed']))

            z_info = self.get_znumber_for_closure(localid, pos, closed_yyyymmdd)

            case = {
                'localid': localid,
                'pos': pos,
                'closed': closed_yyyymmdd,
                'znumber': z_info['znumber'] if z_info else None,
                'closed_datetime': z_info['closed'] if z_info else None,
                'orphans': int(row['details'].split()[1]) if 'Encontrados' in row['details'] else 0
            }

            cases.append(case)
            print(f"Local {localid} | POS {pos} | Z{z_info['znumber'] if z_info else '?'} | Closed {closed_yyyymmdd} | Orphans: {case['orphans']}")

        return pd.DataFrame(cases)

    def process_with_cleanup(self):
        """
        Ejecuta el flujo completo:
        1. Identificar anomalias
        2. Limpiar detalles hurfanos
        3. Generar comandos ajustados
        """

        print("\n" + "="*70)
        print("PROCESAMIENTO CON LIMPIEZA DE DETALLES HURFANOS")
        print("="*70)

        # Paso 1: Identificar anomalias desde el CSV existente
        print("\n[PASO 1] Identificando anomalias...")
        df_problematic = self.identify_anomalies_from_csv()

        if len(df_problematic) == 0:
            print("\n[OK] No hay cases con FAILs. Proceso completado.")
            return

        # Paso 2: Limpiar detalles hurfanos
        print("\n[PASO 2] Limpiando detalles hurfanos...")
        cleanup_results = []
        for idx, row in df_problematic.iterrows():
            result = self.cleaner.delete_orphan_details(
                int(row['localid']),
                int(row['pos']),
                str(int(row['closed'])),
                dry_run=False
            )
            cleanup_results.append({
                'localid': int(row['localid']),
                'pos': int(row['pos']),
                'closed': str(int(row['closed'])),
                'status': result.get('status'),
                'deleted': result.get('deleted', 0)
            })

        df_cleanup = pd.DataFrame(cleanup_results)
        df_cleanup.to_csv('cleanup_executed.csv', index=False)
        print(f"\n[OK] Limpieza completada. Resultados guardados en: cleanup_executed.csv")

        # Paso 3: Generar comandos de carga
        print("\n[PASO 3] Generando comandos de carga...")
        commands = self._generate_commands_based_on_z(df_problematic)

        with open('missing_cierres_commands_cleaned.sh', 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Comandos generados despues de limpieza de detalles hurfanos\n")
            f.write(f"# Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            for cmd in commands:
                f.write(f"# Local {cmd['localid']} | POS {cmd['pos']} | Z{cmd['znumber']} | Closed {cmd['closed']}\n")
                f.write(f"{cmd['command']}\n\n")

        print(f"[OK] Comandos guardados en: missing_cierres_commands_cleaned.sh")
        print(f"   Total comandos: {len(commands)}")

        return {
            'problematic_cases': df_problematic,
            'cleanup_results': df_cleanup,
            'commands': commands
        }

    def _generate_commands_based_on_z(self, df_cases):
        """
        Genera comandos usando Z como identificador en lugar de closed.

        El Z (znumber) es mejor para:
        1. Identificar cierres anomalamente cercanos
        2. Reproducir el mismo cierre en otro ambiente
        3. Auditoria y trazabilidad
        """

        commands = []

        for idx, row in df_cases.iterrows():
            localid = int(row['localid'])
            pos = int(row['pos'])
            closed_yyyymmdd = str(int(row['closed']))

            # El comando sigue usando closed porque run.py esta configurado asi
            # Pero documentamos el Z para referencia
            cmd = f"python run.py --localid {localid} --pos {pos} --fecha_ini {closed_yyyymmdd} --fecha_fin {closed_yyyymmdd}"

            commands.append({
                'localid': localid,
                'pos': pos,
                'closed': closed_yyyymmdd,
                'znumber': int(row['znumber']) if pd.notna(row['znumber']) else None,
                'command': cmd
            })

        return commands

    def generate_final_report(self, process_result):
        """Genera reporte final del proceso"""

        print("\n" + "="*70)
        print("REPORTE FINAL DE PROCESAMIENTO")
        print("="*70)

        df_problems = process_result['problematic_cases']
        df_cleanup = process_result['cleanup_results']

        print(f"\n[*] RESUMEN:")
        print(f"  - Casos con FAILs: {len(df_problems)}")
        print(f"  - Registros limpiados: {df_cleanup['deleted'].sum()}")
        print(f"  - Comandos generados: {len(process_result['commands'])}")

        print(f"\n[*] DETALLES:")
        for idx, row in df_cleanup.iterrows():
            print(f"  Local {int(row['localid'])} | POS {int(row['pos'])} | {int(row['deleted'])} registros eliminados")

        print(f"\n[OK] Archivos generados:")
        print(f"  - cleanup_executed.csv (resultados de limpieza)")
        print(f"  - missing_cierres_commands_cleaned.sh (comandos listos para ejecutar)")


def main():
    processor = CleanupAwareProcessor()
    result = processor.process_with_cleanup()

    if result:
        processor.generate_final_report(result)
        print("\n" + "="*70)
        print("[OK] PROCESO COMPLETADO EXITOSAMENTE")
        print("="*70)
        print("\n[*] PROXIMOS PASOS:")
        print("  1. Revisar cleanup_executed.csv para confirmar limpieza")
        print("  2. Revisar missing_cierres_commands_cleaned.sh")
        print("  3. Ejecutar: bash missing_cierres_commands_cleaned.sh")
        print("  4. Obtener aprobacion PROD antes de ejecutar")


if __name__ == "__main__":
    main()
