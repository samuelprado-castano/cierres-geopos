"""
Ejemplos de uso manual de los scripts de cierres faltantes
Ejecutar con: python example_manual_usage.py
"""
import pandas as pd
from src.missing_cierres import MissingCierresProcessor, print_missing_summary
from src.qa_missing_cierres import QAMissingCierres

def ejemplo_1_buscar_faltantes():
    """Ejemplo 1: Solo buscar cierres faltantes"""
    print("\n" + "="*80)
    print("EJEMPLO 1: Buscar Cierres Faltantes")
    print("="*80)

    processor = MissingCierresProcessor()

    # Buscar cierres de enero 2026
    df_missing = processor.find_missing_cierres("20260101", "20260131")

    # Imprimir resumen
    print_missing_summary(df_missing)

    # Mostrar primeros registros
    if not df_missing.empty:
        print("\n📋 Primeros 5 cierres faltantes:")
        print(df_missing[['localid', 'pos', 'closed', 'id', 'znumber']].head())

    return df_missing


def ejemplo_2_filtrar_por_local(df_missing, localid):
    """Ejemplo 2: Filtrar cierres faltantes por local específico"""
    print("\n" + "="*80)
    print(f"EJEMPLO 2: Filtrar cierres faltantes del Local {localid}")
    print("="*80)

    df_local = df_missing[df_missing['localid'] == localid]

    if df_local.empty:
        print(f"No hay cierres faltantes para el local {localid}")
        return df_local

    print(f"\nCierres faltantes del Local {localid}:")
    print(df_local[['pos', 'closed', 'opened', 'ticketnumber_opened', 'ticketnumber_closed']])

    return df_local


def ejemplo_3_qa_para_un_cierre(localid, pos, closed, opened, ticketnumber_opened, ticketnumber_closed):
    """Ejemplo 3: Ejecutar QA para un cierre específico"""
    print("\n" + "="*80)
    print(f"EJEMPLO 3: QA para Cierre Específico")
    print("="*80)

    qa = QAMissingCierres()

    # Ejecutar QA para un cierre
    qa.run_qa_for_cierre(
        id=1,
        localid=localid,
        pos=pos,
        opened=opened,
        closed=closed,
        ticketnumber_opened=ticketnumber_opened,
        ticketnumber_closed=ticketnumber_closed
    )

    # Mostrar reporte
    qa.print_qa_report()


def ejemplo_4_qa_para_multiples_cierres(df_missing, limite=5):
    """Ejemplo 4: Ejecutar QA solo para algunos cierres (útil para pruebas)"""
    print("\n" + "="*80)
    print(f"EJEMPLO 4: QA para Múltiples Cierres (primeros {limite})")
    print("="*80)

    qa = QAMissingCierres()

    # Ejecutar QA solo para los primeros N cierres
    df_sample = df_missing.head(limite)
    qa.run_qa_for_multiple_cierres(df_sample)
    qa.print_qa_report()

    # Exportar reporte
    qa.export_qa_report(f'qa_report_sample_{limite}.csv')


def ejemplo_5_generar_comandos_por_local(df_missing, target_localid):
    """Ejemplo 5: Generar comandos solo para un local específico"""
    print("\n" + "="*80)
    print(f"EJEMPLO 5: Generar comandos para Local {target_localid}")
    print("="*80)

    # Filtrar por local
    df_local = df_missing[df_missing['localid'] == target_localid]

    if df_local.empty:
        print(f"No hay cierres faltantes para el local {target_localid}")
        return

    # Módulos = None para procesar todos
    modulos = None

    print(f"\nComandos para Local {target_localid}:\n")

    for idx, row in df_local.iterrows():
        localid = int(row['localid'])
        pos = int(row['pos'])
        closed_fmt = pd.Timestamp(row['closed']).strftime('%Y%m%d')

        cmd = f"python run.py --localid {localid} --pos {pos} --fecha_ini {closed_fmt} --fecha_fin {closed_fmt}"
        print(f"  [{idx + 1}] {cmd}")

    # Guardar a archivo local
    filename = f'commands_local_{target_localid}.sh'
    with open(filename, 'w') as f:
        f.write("#!/bin/bash\n")
        for idx, row in df_local.iterrows():
            localid = int(row['localid'])
            pos = int(row['pos'])
            closed_fmt = pd.Timestamp(row['closed']).strftime('%Y%m%d')
            cmd = f"python run.py --localid {localid} --pos {pos} --fecha_ini {closed_fmt} --fecha_fin {closed_fmt}"
            f.write(f"{cmd}\n")

    print(f"\n✓ Guardado en {filename}")


def ejemplo_6_estadisticas(df_missing):
    """Ejemplo 6: Mostrar estadísticas de los cierres faltantes"""
    print("\n" + "="*80)
    print("EJEMPLO 6: Estadísticas de Cierres Faltantes")
    print("="*80)

    if df_missing.empty:
        print("No hay cierres faltantes")
        return

    print(f"\n📊 ESTADÍSTICAS GENERALES:")
    print(f"   Total de cierres faltantes: {len(df_missing)}")
    print(f"   Locales afectados: {df_missing['localid'].nunique()}")
    print(f"   POS afectadas: {df_missing['pos'].nunique()}")

    print(f"\n📊 DESGLOSE POR LOCAL:")
    stats_local = df_missing.groupby('localid').size().sort_values(ascending=False)
    for localid, count in stats_local.items():
        print(f"   Local {localid}: {count} cierres faltantes")

    print(f"\n📊 DESGLOSE POR POS:")
    stats_pos = df_missing.groupby('pos').size().sort_values(ascending=False)
    for pos, count in stats_pos.items():
        print(f"   POS {pos}: {count} cierres faltantes")

    print(f"\n📊 RANGO DE FECHAS:")
    fecha_min = df_missing['closed'].min()
    fecha_max = df_missing['closed'].max()
    print(f"   Primer cierre faltante: {fecha_min}")
    print(f"   Último cierre faltante: {fecha_max}")


def ejemplo_7_comparar_periodos():
    """Ejemplo 7: Comparar cierres faltantes en diferentes períodos"""
    print("\n" + "="*80)
    print("EJEMPLO 7: Comparar Múltiples Períodos")
    print("="*80)

    processor = MissingCierresProcessor()

    periodos = [
        ("20260101", "20260131", "Enero 2026"),
        ("20260201", "20260228", "Febrero 2026"),
    ]

    print("\n")
    for fecha_ini, fecha_fin, label in periodos:
        df = processor.find_missing_cierres(fecha_ini, fecha_fin)
        print(f"   {label}: {len(df)} cierres faltantes")


# ============================================================================
# EJECUTAR EJEMPLOS
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("EJEMPLOS DE USO DEL PROCESADOR DE CIERRES FALTANTES")
    print("="*80)

    # EJEMPLO 1: Buscar faltantes
    df_missing = ejemplo_1_buscar_faltantes()

    if not df_missing.empty:
        # EJEMPLO 2: Filtrar por local
        if df_missing['localid'].min() > 0:
            ejemplo_2_filtrar_por_local(df_missing, df_missing['localid'].iloc[0])

        # EJEMPLO 3: QA para un cierre específico
        # (comentar para no ejecutar QA completo, es lento)
        # primer_cierre = df_missing.iloc[0]
        # ejemplo_3_qa_para_un_cierre(
        #     primer_cierre['localid'],
        #     primer_cierre['pos'],
        #     primer_cierre['closed'],
        #     primer_cierre['opened'],
        #     primer_cierre['ticketnumber_opened'],
        #     primer_cierre['ticketnumber_closed']
        # )

        # EJEMPLO 4: QA para algunos cierres de prueba
        # ejemplo_4_qa_para_multiples_cierres(df_missing, limite=3)

        # EJEMPLO 5: Generar comandos por local
        # ejemplo_5_generar_comandos_por_local(df_missing, df_missing['localid'].iloc[0])

        # EJEMPLO 6: Estadísticas
        ejemplo_6_estadisticas(df_missing)

        # EJEMPLO 7: Comparar períodos
        ejemplo_7_comparar_periodos()

    print("\n" + "="*80)
    print("✓ Ejemplos completados")
    print("="*80 + "\n")
