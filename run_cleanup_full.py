#!/usr/bin/env python3
"""
Ejecutor completo del flujo de limpieza de cierres faltantes.

UN SOLO COMANDO HACE TODO:
1. Analiza anomalías por Z
2. Limpia detalles huérfanos
3. Genera comandos listos para ejecutar

Uso:
    python run_cleanup_full.py
"""

import sys
import subprocess
from datetime import datetime
import pandas as pd

class FullCleanupRunner:
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.results = {}

    def print_header(self, title):
        print("\n" + "="*70)
        print(f"  {title}")
        print("="*70)

    def print_success(self, msg):
        print(f"[OK] {msg}")

    def print_error(self, msg):
        print(f"[ERROR] {msg}")

    def print_info(self, msg):
        print(f"[INFO] {msg}")

    def step_1_analyze_anomalies(self):
        """Paso 1: Analizar anomalías"""
        self.print_header("PASO 1/3: ANALIZAR ANOMALIAS")

        try:
            print("\n[*] Analizando secuencia Z de cierres faltantes...")
            result = subprocess.run(
                ["python", "analyze_anomalies.py"],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                self.print_success("Analisis completado")
                self.print_info("Archivo: anomaly_report.csv")

                # Mostrar resumen
                try:
                    df = pd.read_csv('anomaly_report.csv')
                    print(f"\n[*] Casos analizados: {len(df)}")
                    for idx, row in df.iterrows():
                        rec = row['recommendation'][:30] if pd.notna(row['recommendation']) else "?"
                        print(f"   {row['localid']}/{row['pos']} - {rec}...")
                except:
                    pass

                self.results['analyze'] = 'SUCCESS'
                return True
            else:
                self.print_error(f"Analisis fallo")
                print(result.stderr)
                self.results['analyze'] = 'ERROR'
                return False

        except subprocess.TimeoutExpired:
            self.print_error("Analisis tomo demasiado tiempo")
            self.results['analyze'] = 'TIMEOUT'
            return False
        except Exception as e:
            self.print_error(f"Error: {str(e)}")
            self.results['analyze'] = 'EXCEPTION'
            return False

    def step_2_cleanup_orphans(self):
        """Paso 2: Limpiar detalles huérfanos"""
        self.print_header("PASO 2/3: LIMPIAR DETALLES HURFANOS")

        try:
            print("\n[*] Limpiando detalles hurfanos...")
            result = subprocess.run(
                ["python", "cleanup_orphan_details.py"],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0 or "No hay detalles" in result.stdout:
                self.print_success("Limpieza completada")
                self.print_info("Archivo: cleanup_results.csv")

                # Mostrar resumen
                try:
                    df = pd.read_csv('cleanup_results.csv')
                    total = df['deleted'].sum()
                    self.print_success(f"Total registros eliminados: {total}")
                    for idx, row in df.iterrows():
                        if row['deleted'] > 0:
                            print(f"   {row['localid']}/{row['pos']}: {row['deleted']} registros")
                except:
                    pass

                self.results['cleanup'] = 'SUCCESS'
                return True
            else:
                self.print_error("Limpieza fallo")
                print(result.stderr)
                self.results['cleanup'] = 'ERROR'
                return False

        except subprocess.TimeoutExpired:
            self.print_error("Limpieza tomo demasiado tiempo")
            self.results['cleanup'] = 'TIMEOUT'
            return False
        except Exception as e:
            self.print_error(f"Error: {str(e)}")
            self.results['cleanup'] = 'EXCEPTION'
            return False

    def step_3_generate_commands(self):
        """Paso 3: Generar comandos limpios"""
        self.print_header("PASO 3/3: GENERAR COMANDOS")

        try:
            print("\n[*] Generando comandos de carga...")
            result = subprocess.run(
                ["python", "process_with_cleanup.py"],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                self.print_success("Comandos generados")
                self.print_info("Archivo: missing_cierres_commands_cleaned.sh")
                self.print_info("Archivo: cleanup_executed.csv")

                # Contar comandos
                try:
                    with open('missing_cierres_commands_cleaned.sh', 'r') as f:
                        commands = [l for l in f.readlines() if l.startswith('python run.py')]
                    self.print_success(f"Total comandos generados: {len(commands)}")
                except:
                    pass

                self.results['generate'] = 'SUCCESS'
                return True
            else:
                self.print_error("Generacion de comandos fallo")
                print(result.stderr)
                self.results['generate'] = 'ERROR'
                return False

        except subprocess.TimeoutExpired:
            self.print_error("Generacion tomo demasiado tiempo")
            self.results['generate'] = 'TIMEOUT'
            return False
        except Exception as e:
            self.print_error(f"Error: {str(e)}")
            self.results['generate'] = 'EXCEPTION'
            return False

    def run_full_workflow(self):
        """Ejecuta el flujo completo"""
        self.print_header("FLUJO COMPLETO DE LIMPIEZA")
        print(f"Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        success = True

        # Paso 1
        if not self.step_1_analyze_anomalies():
            success = False

        # Paso 2
        if success and not self.step_2_cleanup_orphans():
            success = False

        # Paso 3
        if success and not self.step_3_generate_commands():
            success = False

        return success

    def print_final_report(self, success):
        """Reporte final"""
        self.print_header("RESUMEN FINAL")

        print(f"\n[*] ESTADO DE PASOS:")
        steps = ['Analisis', 'Limpieza', 'Generacion']
        keys = ['analyze', 'cleanup', 'generate']
        for step, key in zip(steps, keys):
            status = self.results.get(key, 'SKIPPED')
            icon = "[OK]" if status == 'SUCCESS' else "[SKIP]" if status == 'SKIPPED' else "[FAIL]"
            print(f"  {icon} {step}: {status}")

        if success:
            print(f"\n{'='*70}")
            print(f"[SUCCESS] FLUJO COMPLETADO EXITOSAMENTE")
            print(f"{'='*70}")

            print(f"\n[*] ARCHIVOS GENERADOS:")
            print(f"  - anomaly_report.csv")
            print(f"  - cleanup_results.csv")
            print(f"  - cleanup_executed.csv")
            print(f"  - missing_cierres_commands_cleaned.sh")

            print(f"\n[*] PROXIMOS PASOS:")
            print(f"  1. Revisar missing_cierres_commands_cleaned.sh")
            print(f"  2. Obtener aprobacion PROD")
            print(f"  3. Ejecutar: bash missing_cierres_commands_cleaned.sh")
            print(f"  4. Validar con queries SQL")

            return True
        else:
            print(f"\n{'='*70}")
            print(f"[FAILED] FLUJO FALLO")
            print(f"{'='*70}")
            print(f"\nVerifica los logs anteriores para errores")
            return False


def main():
    runner = FullCleanupRunner()

    # Ejecutar flujo
    success = runner.run_full_workflow()

    # Reporte
    runner.print_final_report(success)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
