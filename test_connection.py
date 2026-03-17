"""
Script para verificar que las conexiones y queries funcionan correctamente
Ejecutar: python test_connection.py
"""
import pandas as pd
from src.config import DB_URL_GEOCOM, DB_URL_DW
import sqlalchemy as sa

def test_geocom_connection():
    """Prueba conexión a GEOCOM"""
    print("\n" + "="*80)
    print("TEST 1: Conexión a GEOCOM")
    print("="*80)

    try:
        engine = sa.create_engine(DB_URL_GEOCOM, fast_executemany=True)

        # Verificar estructura de tabla totals
        query = """
        SELECT TOP 5
            localid,
            pos,
            closed,
            opened,
            subclass,
            znumber,
            ticketsequencenumber
        FROM totals
        WHERE subclass = 'postotal'
        AND localid BETWEEN 100 AND 999
        ORDER BY closed DESC
        """

        df = pd.read_sql_query(query, engine)

        if df.empty:
            print("⚠️ Conexión OK, pero no hay datos en totals")
        else:
            print("✓ Conexión OK")
            print(f"✓ Tabla totals tiene datos")
            print(f"\nÚltimos 5 cierres en geocom:")
            print(df.to_string(index=False))

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_dw_connection():
    """Prueba conexión a DW"""
    print("\n" + "="*80)
    print("TEST 2: Conexión a DW")
    print("="*80)

    try:
        engine = sa.create_engine(DB_URL_DW, fast_executemany=True)

        # Verificar estructura de tabla cierres
        query = """
        SELECT TOP 5
            id,
            localid,
            pos,
            closed
        FROM modelo_ventas_rauco.cierres
        ORDER BY closed DESC
        """

        df = pd.read_sql_query(query, engine)

        if df.empty:
            print("⚠️ Conexión OK, pero no hay datos en cierres")
        else:
            print("✓ Conexión OK")
            print(f"✓ Tabla cierres tiene datos")
            print(f"\nÚltimos 5 cierres en DW:")
            print(df.to_string(index=False))

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_missing_cierres_query():
    """Prueba la query de cierres faltantes"""
    print("\n" + "="*80)
    print("TEST 3: Query de Cierres Faltantes")
    print("="*80)

    try:
        eng_geocom = sa.create_engine(DB_URL_GEOCOM, fast_executemany=True)
        eng_dw = sa.create_engine(DB_URL_DW, fast_executemany=True)

        # Query de geocom
        query_geocom = """
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
            curr.closed
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
        AND CAST(CONVERT(VARCHAR, curr.closed, 112) AS INT) BETWEEN 20260101 AND 20260131
        AND curr.localid BETWEEN 100 AND 999
        """

        df_geocom = pd.read_sql_query(query_geocom, eng_geocom)

        if df_geocom.empty:
            print("⚠️ No hay cierres en geocom para enero 2026")
        else:
            print(f"✓ Query de geocom OK: {len(df_geocom)} cierres")
            print(f"\nÚltimos 3 cierres de geocom:")
            print(df_geocom.tail(3).to_string(index=False))

        # Query de DW
        query_dw = """
        SELECT DISTINCT id
        FROM modelo_ventas_rauco.cierres
        WHERE CAST(CONVERT(VARCHAR, closed, 112) AS INT) BETWEEN 20260101 AND 20260131
        """

        df_dw = pd.read_sql_query(query_dw, eng_dw)

        if df_dw.empty:
            print("\n⚠️ No hay cierres en DW para enero 2026")
        else:
            print(f"\n✓ Query de DW OK: {len(df_dw)} cierres")

        # Cruce
        if not df_geocom.empty and not df_dw.empty:
            missing = df_geocom[~df_geocom['id'].isin(df_dw['id'])]
            print(f"\n✓ Cruce realizado: {len(missing)} cierres faltantes")
        elif not df_geocom.empty:
            print(f"\n✓ Todos los cierres de geocom faltan en DW: {len(df_geocom)} cierres")

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*80)
    print("PRUEBAS DE CONEXIÓN Y QUERIES")
    print("="*80)

    results = []

    # TEST 1
    results.append(("Conexión GEOCOM", test_geocom_connection()))

    # TEST 2
    results.append(("Conexión DW", test_dw_connection()))

    # TEST 3
    results.append(("Query Cierres Faltantes", test_missing_cierres_query()))

    # RESUMEN
    print("\n" + "="*80)
    print("RESUMEN")
    print("="*80)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print("\n✓ Todas las pruebas pasaron. Listo para ejecutar process_missing_cierres.py")
    else:
        print("\n✗ Algunas pruebas fallaron. Revisar los errores arriba.")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
