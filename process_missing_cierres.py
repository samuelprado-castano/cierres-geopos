"""
Script principal para procesar cierres faltantes
1. Busca cierres faltantes entre geocom.totals y DW.cierres
2. Ejecuta QA para validar los datos
3. Prepara los comandos para ejecutar run.py (sin ejecutarlos aún)
"""
import sys
import os
import pandas as pd
from datetime import datetime
from src.missing_cierres import MissingCierresProcessor, print_missing_summary
from src.qa_missing_cierres import QAMissingCierres

def format_date_to_yyyymmdd(date_str):
    """Convierte string de fecha a formato YYYYMMDD"""
    try:
        dt = pd.Timestamp(date_str)
        return dt.strftime('%Y%m%d')
    except:
        return date_str

def generate_run_py_commands(df_missing, modulos=None):
    """
    Genera los comandos para ejecutar run.py para cada cierre faltante
    Usa --z (znumber) en lugar de fechas para apuntar directamente al cierre específico
    Si el mismo Z se repite (reinicio del contador), incluye --fecha_ini y --fecha_fin para desambiguar
    Si modulos es None, procesa todos los módulos automáticamente
    """
    commands = []

    # Detectar Z duplicados (caso de reinicio del contador)
    z_duplicates = df_missing.groupby(['localid', 'pos', 'znumber']).size()
    z_duplicates = z_duplicates[z_duplicates > 1]

    print("\n" + "=" * 100)
    print("COMANDOS PARA EJECUTAR run.py (Modo Z - por znumber)")
    print("=" * 100)

    if modulos is None:
        print(f"\nMódulos a ejecutar: TODOS (VENTAS, MEDIOS_PAGO, REDONDEOS, DEPOSITOS, GUIAS)")
        modulos_str = ""
    else:
        modulos_str = ' '.join(modulos)
        print(f"\nMódulos a ejecutar: {', '.join(modulos)}")

    print(f"Total de cierres a procesar: {len(df_missing)}\n")

    for idx, (_, row) in enumerate(df_missing.iterrows()):
        localid = int(row['localid'])
        pos = int(row['pos'])
        znumber = int(row['znumber'])
        closed_fmt = pd.Timestamp(row['closed']).strftime('%Y%m%d')

        # Verificar si este (localid, pos, z) es duplicado
        is_duplicate_z = (localid, pos, znumber) in z_duplicates.index

        if modulos_str:
            cmd = f"python run.py --modulos {modulos_str} --localid {localid} --pos {pos} --z {znumber}"
            cmd += f" --fecha_ini {closed_fmt} --fecha_fin {closed_fmt}"

        else:
            cmd = f"python run.py --localid {localid} --pos {pos} --z {znumber}"
            cmd += f" --fecha_ini {closed_fmt} --fecha_fin {closed_fmt}"

        commands.append({
            'localid': localid,
            'pos': pos,
            'znumber': znumber,
            'closed': closed_fmt,
            'command': cmd
        })

        warning = " [ADVERTENCIA: Z duplicado detectado - se incluye fecha]" if is_duplicate_z else ""
        print(f"[{idx + 1}/{len(df_missing)}] Local {localid} | POS {pos} | Z {znumber} | Closed {closed_fmt}{warning}")
        print(f"      $ {cmd}\n")

    print("=" * 100)
    if z_duplicates.size > 0:
        print(f"\n[ADVERTENCIA] Se detectaron Z numbers duplicados (reinicio del contador):")
        print(f"              Se agregó --fecha_ini y --fecha_fin automáticamente para desambiguar.\n")
    print(f"[ADVERTENCIA] NO EJECUTANDO AÚN - Estos comandos se ejecutarán en PROD")
    print(f"Total de ejecuciones requeridas: {len(commands)}\n")

    return commands

def save_commands_to_file(commands, filename='missing_cierres_commands.sh'):
    """
    Guarda los comandos en un archivo shell script
    """
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("#!/bin/bash\n")
        f.write("# Script generado automáticamente para procesar cierres faltantes\n")
        f.write(f"# Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("# Modo: Ejecución directa por Z (znumber) - sin fechas\n")
        f.write("# NOTA: Ejecutar solo en PROD después de QA\n\n")

        for cmd_dict in commands:
            f.write(f"# Local {cmd_dict['localid']} | POS {cmd_dict['pos']} | Z {cmd_dict['znumber']} | Closed {cmd_dict['closed']}\n")
            f.write(f"{cmd_dict['command']}\n\n")

    print(f"[OK] Comandos guardados en {filename}")
    return filename

def main():
    """
    Flujo principal:
    1. Buscar cierres faltantes
    2. Ejecutar QA
    3. Generar comandos (sin ejecutar)
    """
    print("\n" + "=" * 100)
    print("PROCESADOR DE CIERRES FALTANTES")
    print("=" * 100)

    # Parámetros
    fecha_ini = "20260101"  # Enero 2026
    fecha_fin = "20260317"  # 31 de Enero 2026

    print(f"\nPeríodo a analizar: {fecha_ini[0:4]}-{fecha_ini[4:6]}-{fecha_ini[6:8]} a {fecha_fin[0:4]}-{fecha_fin[4:6]}-{fecha_fin[6:8]}")

    # PASO 1: Buscar cierres faltantes
    print("\n" + "-" * 100)
    print("PASO 1: Identificando cierres faltantes")
    print("-" * 100)

    processor = MissingCierresProcessor()
    df_missing = processor.find_missing_cierres(fecha_ini, fecha_fin)

    # Resumen
    print_missing_summary(df_missing)

    if df_missing.empty:
        print("[OK] No hay cierres faltantes para este período")
        return

    # # PASO 2: Ejecutar QA
    # print("\n" + "-" * 100)
    # print("PASO 2: Validando datos de cierres faltantes (QA)")
    # print("-" * 100)

    # qa = QAMissingCierres()
    # qa.run_qa_for_multiple_cierres(df_missing)
    # qa_report = qa.print_qa_report()

    # Guardar reporte QA
    # qa.export_qa_report('qa_missing_cierres.csv')

    # PASO 3: Generar comandos para run.py (sin ejecutar)
    print("\n" + "-" * 100)
    print("PASO 3: Generando comandos para run.py")
    print("-" * 100)

    # Definir módulos a ejecutar
    # Opciones:
    # - None: procesa todos (VENTAS, MEDIOS_PAGO, REDONDEOS, DEPOSITOS, GUIAS)
    # - ['VENTAS', 'MEDIOS_PAGO']: procesa solo estos módulos
    modulos = ['VENTAS', 'MEDIOS_PAGO', 'REDONDEOS', 'DEPOSITOS', 'GUIAS']

    commands = generate_run_py_commands(df_missing, modulos)

    # Guardar comandos en archivo
    script_filename = save_commands_to_file(commands)

    # Resumen final
    print("\n" + "=" * 100)
    print("RESUMEN FINAL")
    print("=" * 100)
    print(f"\n[OK] Cierres faltantes identificados: {len(df_missing)}")
    print(f"[OK] Modo: Ejecución directa por Z (znumber) - sin usar fechas")
    print(f"[OK] Reportes generados:")
    print(f"   - qa_missing_cierres.csv (Reporte QA detallado)")
    print(f"   - {script_filename} (Comandos para ejecutar en PROD)")
    print(f"\n[ADVERTENCIA] PRÓXIMOS PASOS:")
    print(f"   1. Revisar qa_missing_cierres.csv para validar los datos")
    print(f"   2. Si todo OK, ejecutar {script_filename} en PROD")
    print(f"   3. Los datos se cargarán en DW después de ejecutar los comandos")
    print(f"   4. Cada comando ejecuta solo el cierre especificado (Z) para la tienda/caja")
    print("\n" + "=" * 100 + "\n")

if __name__ == "__main__":
    import io
    # Asegurar UTF-8 en stdout/stderr
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    main()
