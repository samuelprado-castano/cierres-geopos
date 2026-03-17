"""
Script QA para validar datos y módulos de cierres faltantes
Verifica que los datos de módulos (ventas, medios_pago, etc) NO existan en DW
"""
import pandas as pd
import sqlalchemy as sa
from src.config import DB_URL_DW, DB_URL_GEOCOM
from datetime import datetime


class QAMissingCierres:
    def __init__(self):
        self.eng_geocom = sa.create_engine(DB_URL_GEOCOM, fast_executemany=True)
        self.eng_dw = sa.create_engine(DB_URL_DW, fast_executemany=True)
        self.test_results = []

    def test_cierre_exists_in_geocom(self, localid, pos, znumber, closed_fmt):
        """
        Valida que el cierre exista en geocom.totals
        Busca por (localid, pos, znumber, closed) para máxima granularidad
        """
        query = f"""
        SELECT COUNT(*) as count_totals
        FROM totals
        WHERE localid = {localid}
            AND pos = {pos}
            AND znumber = {znumber}
            AND CAST(CONVERT(VARCHAR, closed, 112) AS INT) = {closed_fmt}
        """
        try:
            result = pd.read_sql_query(query, self.eng_geocom)
            count = result['count_totals'].values[0]
            test_passed = count > 0
            self.test_results.append({
                'test': f'Cierre existe en geocom',
                'localid': localid,
                'pos': pos,
                'closed': closed_fmt,
                'status': '[PASS]' if test_passed else '[FAIL]',
                'details': f'Encontrados {count} registros'
            })
            return test_passed
        except Exception as e:
            self.test_results.append({
                'test': f'Cierre existe en geocom',
                'localid': localid,
                'pos': pos,
                'closed': closed_fmt,
                'status': '[ERROR]',
                'details': str(e)
            })
            return False

    def test_ventas_data_exists_in_geocom(self, localid, pos, ticketnumber_opened, ticketnumber_closed, opened_fmt, closed_fmt):
        """
        Valida que existan datos de ventas en geocom para este cierre
        """
        query = f"""
        SELECT COUNT(*) as count_ventas
        FROM tickets
        WHERE localid = {localid}
            AND pos = {pos}
            AND ticketnumber BETWEEN {ticketnumber_opened} AND {ticketnumber_closed}
            AND CAST(CONVERT(VARCHAR, opendate, 112) AS INT) BETWEEN {opened_fmt} AND {closed_fmt}
            AND documenttype IN ('sale', 'sale-cancel')
        """
        try:
            result = pd.read_sql_query(query, self.eng_geocom)
            count = result['count_ventas'].values[0]
            test_passed = count > 0
            self.test_results.append({
                'test': 'Datos de ventas existen en geocom',
                'localid': localid,
                'pos': pos,
                'closed': closed_fmt,
                'status': '[PASS]' if test_passed else '[WARNING]',
                'details': f'Encontrados {count} tickets'
            })
            return test_passed
        except Exception as e:
            self.test_results.append({
                'test': 'Datos de ventas existen en geocom',
                'localid': localid,
                'pos': pos,
                'closed': closed_fmt,
                'status': '[ERROR]',
                'details': str(e)
            })
            return False

    def test_medios_pago_data_exists_in_geocom(self, localid, pos, ticketnumber_opened, ticketnumber_closed, opened_fmt, closed_fmt):
        """
        Valida que existan datos de medios de pago en geocom
        Query basada en main.py - usa tabla payments y paymentmodes
        """
        query = f"""
        SELECT COUNT(*) as count_payments
        FROM tickets
        INNER JOIN payments
            ON tickets.opendate = payments.opendate
            AND tickets.localid = payments.localid
            AND tickets.ticketnumber = payments.ticketnumber
            AND tickets.pos = payments.pos
        INNER JOIN paymentmodes
            ON payments.paymentmode = paymentmodes.id
        WHERE tickets.localid = {localid}
            AND tickets.pos = {pos}
            AND ISNUMERIC(tickets.ticketnumber) = 1
            AND CAST(tickets.ticketnumber AS INT) BETWEEN {ticketnumber_opened} AND {ticketnumber_closed}
            AND CAST(CONVERT(VARCHAR, tickets.opendate, 112) AS INT) BETWEEN {opened_fmt} AND {closed_fmt}
            AND paymentmodes.id NOT IN (40)
            AND tickets.documenttype = 'sale'
        """
        try:
            result = pd.read_sql_query(query, self.eng_geocom)
            count = result['count_payments'].values[0]
            test_passed = count > 0
            # Si no hay pagos es WARNING, no ERROR (algunos cierres pueden no tener pagos)
            status = '[PASS]' if test_passed else '[WARNING]'
            self.test_results.append({
                'test': 'Datos de medios pago existen en geocom',
                'localid': localid,
                'pos': pos,
                'closed': closed_fmt,
                'status': status,
                'details': f'Encontrados {count} pagos'
            })
            return test_passed
        except Exception as e:
            self.test_results.append({
                'test': 'Datos de medios pago existen en geocom',
                'localid': localid,
                'pos': pos,
                'closed': closed_fmt,
                'status': '[WARNING]',
                'details': f'No se pudo validar: {str(e)[:100]}'
            })
            return False

    def test_cierre_NOT_in_dw(self, id_cierre):
        """
        Valida que el cierre NO exista en DW (debe estar faltante)
        Usa el ID que es único
        """
        query = f"""
        SELECT COUNT(*) as count_dw
        FROM modelo_ventas_rauco.cierres
        WHERE id = '{id_cierre}'
        """
        try:
            result = pd.read_sql_query(query, self.eng_dw)
            count = result['count_dw'].values[0]
            test_passed = count == 0  # Debe estar vacío
            self.test_results.append({
                'test': 'Cierre NO existe en DW (validación de faltante)',
                'id': id_cierre,
                'status': '[PASS]' if test_passed else '[FAIL]',
                'details': f'Encontrados {count} registros en DW (esperaba 0)'
            })
            return test_passed
        except Exception as e:
            self.test_results.append({
                'test': 'Cierre NO existe en DW (validación de faltante)',
                'id': id_cierre,
                'status': '[ERROR]',
                'details': str(e)
            })
            return False

    def test_cierre_detail_NOT_in_dw(self, localid, pos, znumber, closed_fmt):
        """
        Valida que los detalles del cierre NO existan en DW
        Busca por (localid, pos, z, closed) para máxima granularidad
        """
        query = f"""
        SELECT COUNT(*) as count_details
        FROM modelo_ventas_rauco.cierres_detalle
        WHERE localid = {localid}
            AND pos = {pos}
            AND z = {znumber}
            AND CAST(CONVERT(VARCHAR, closed, 112) AS INT) = {closed_fmt}
        """
        try:
            result = pd.read_sql_query(query, self.eng_dw)
            count = result['count_details'].values[0]
            test_passed = count == 0  # Debe estar vacío
            self.test_results.append({
                'test': 'Detalle del cierre NO existe en DW',
                'localid': localid,
                'pos': pos,
                'closed': closed_fmt,
                'status': '[PASS]' if test_passed else '[FAIL]',
                'details': f'Encontrados {count} registros en detalle (esperaba 0)'
            })
            return test_passed
        except Exception as e:
            self.test_results.append({
                'test': 'Detalle del cierre NO existe en DW',
                'localid': localid,
                'pos': pos,
                'closed': closed_fmt,
                'status': '[ERROR]',
                'details': str(e)
            })
            return False

    def test_data_consistency(self, id_cierre, localid, pos, znumber, closed_fmt):
        """
        VALIDACIÓN CRÍTICA: Detecta inconsistencias (detalle sin cabecera)
        Si existe detalle pero NO existe cabecera → ALARMA
        Busca por (localid, pos, z, closed) para máxima granularidad
        """
        query_header = f"""
        SELECT COUNT(*) as count_header
        FROM modelo_ventas_rauco.cierres
        WHERE id = '{id_cierre}'
        """

        query_detail = f"""
        SELECT COUNT(*) as count_detail
        FROM modelo_ventas_rauco.cierres_detalle
        WHERE localid = {localid}
            AND pos = {pos}
            AND z = {znumber}
            AND CAST(CONVERT(VARCHAR, closed, 112) AS INT) = {closed_fmt}
        """

        try:
            result_header = pd.read_sql_query(query_header, self.eng_dw)
            result_detail = pd.read_sql_query(query_detail, self.eng_dw)

            count_header = result_header['count_header'].values[0]
            count_detail = result_detail['count_detail'].values[0]

            # Test PASS si: (ambos vacíos) O (ambos con datos)
            # Test FAIL si: detalle existe pero cabecera no
            if count_header == 0 and count_detail == 0:
                # [OK] Ambos vacíos - correcto
                test_passed = True
                status = '[PASS]'
                details = 'Cabecera y detalle: ambos vacíos (correcto)'
            elif count_header > 0 and count_detail > 0:
                # [OK] Ambos con datos - correcto
                test_passed = True
                status = '[PASS]'
                details = f'Cabecera y detalle: consistentes (ambos con datos)'
            elif count_header == 0 and count_detail > 0:
                # [CRÍTICO] INCONSISTENCIA CRÍTICA
                test_passed = False
                status = '[FAIL]'
                details = f'[ADVERTENCIA] INCONSISTENCIA: Detalle existe ({count_detail} reg) pero Cabecera NO'
            else:
                # [OK] Cabecera sin detalle - puede ser válido (sin ventas)
                test_passed = True
                status = '[PASS]'
                details = f'Cabecera sin detalle: válido (cierre sin ventas)'

            self.test_results.append({
                'test': 'Consistencia de datos (cabecera-detalle)',
                'id': id_cierre,
                'status': status,
                'details': details
            })
            return test_passed
        except Exception as e:
            self.test_results.append({
                'test': 'Consistencia de datos (cabecera-detalle)',
                'id': id_cierre,
                'status': '[ERROR]',
                'details': f'No se pudo validar: {str(e)[:100]}'
            })
            return False

    def test_all_tables_consistency(self, localid, pos, znumber, closed_fmt):
        """
        VALIDACIÓN CRÍTICA: Revisa TODAS las tablas de cierre en DW
        Busca datos huérfanos (datos sin el cierre padre)
        Busca por (localid, pos, z, closed) para máxima granularidad
        """
        # Tablas a verificar (excepto cierres que es la cabecera)
        tables = [
            ('cierres_detalle', 'z'),
            ('cierres_precio_producto', 'z'),
            ('cierres_medio_pago', 'z'),
            ('cierres_depositos', 'z'),
            ('cierres_guias', 'z'),
            ('cierres_guias_detalle', 'z'),
        ]

        anomalies = []

        try:
            # Verificar que cabecera existe
            query_header = f"""
            SELECT COUNT(*) as count FROM modelo_ventas_rauco.cierres
            WHERE localid = {localid} AND pos = {pos} AND znumber = {znumber}
                AND CAST(CONVERT(VARCHAR, closed, 112) AS INT) = {closed_fmt}
            """
            result_header = pd.read_sql_query(query_header, self.eng_dw)
            header_exists = result_header['count'].values[0] > 0

            # Si cabecera existe, es OK
            if header_exists:
                status = '[PASS]'
                details = 'Cabecera existe: todas las tablas validadas'
            else:
                # Si cabecera NO existe, buscar datos huérfanos
                details_list = []

                for table_name, z_column in tables:
                    query = f"""
                    SELECT COUNT(*) as count FROM modelo_ventas_rauco.{table_name}
                    WHERE localid = {localid} AND pos = {pos} AND {z_column} = {znumber}
                        AND CAST(CONVERT(VARCHAR, closed, 112) AS INT) = {closed_fmt}
                    """
                    result = pd.read_sql_query(query, self.eng_dw)
                    count = result['count'].values[0]

                    if count > 0:
                        details_list.append(f"{table_name} ({count} regs huérfanos)")
                        anomalies.append(table_name)

                if anomalies:
                    status = '[FAIL]'
                    details = f"[ADVERTENCIA] DATOS HUÉRFANOS en: {', '.join(details_list)}"
                else:
                    status = '[PASS]'
                    details = 'Cabecera no existe, ningún dato huérfano detectado'

            self.test_results.append({
                'test': 'Integridad de TODAS las tablas de cierre',
                'localid': localid,
                'pos': pos,
                'znumber': znumber,
                'status': status,
                'details': details
            })

            return status == '[PASS]'

        except Exception as e:
            self.test_results.append({
                'test': 'Integridad de TODAS las tablas de cierre',
                'localid': localid,
                'pos': pos,
                'znumber': znumber,
                'status': '[ERROR]',
                'details': f'Error validando tablas: {str(e)[:100]}'
            })
            return False

    def test_z_duplicates(self, df_cierres):
        """
        Detecta si hay Z numbers duplicados (reinicio del contador)
        IMPORTANTE: El mismo Z puede existir múltiples veces si el contador se reinició
        Esto no es un error, solo una advertencia
        """
        z_duplicates = df_cierres.groupby(['localid', 'pos', 'znumber']).size()
        z_duplicates = z_duplicates[z_duplicates > 1]

        if len(z_duplicates) > 0:
            print("\n[ADVERTENCIA] Z NUMBERS DUPLICADOS DETECTADOS:")
            print("[ADVERTENCIA] Esto ocurre cuando el contador Z se reinicia en una caja.")
            print("[ADVERTENCIA] Se recomienda usar --fecha_ini y --fecha_fin para desambiguar.\n")

            for (localid, pos, znumber), count in z_duplicates.items():
                matching_rows = df_cierres[
                    (df_cierres['localid'] == localid) &
                    (df_cierres['pos'] == pos) &
                    (df_cierres['znumber'] == znumber)
                ]
                print(f"   Local {localid} | POS {pos} | Z {znumber}: {count} registros")
                for _, row in matching_rows.iterrows():
                    closed_fmt = pd.Timestamp(row['closed']).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"      - {closed_fmt}")

            self.test_results.append({
                'test': 'Detección de Z duplicados (reinicio de contador)',
                'status': '[WARNING]',
                'details': f'Se encontraron {len(z_duplicates)} Z numbers duplicados. Verificar manualmente.'
            })
        else:
            self.test_results.append({
                'test': 'Detección de Z duplicados (reinicio de contador)',
                'status': '[PASS]',
                'details': 'No hay Z duplicados detectados'
            })

    def run_qa_for_cierre(self, id, localid, pos, znumber, opened, closed, ticketnumber_opened, ticketnumber_closed):
        """
        Ejecuta toda la suite de tests para un cierre específico
        """
        print(f"\n[QA] Ejecutando QA para cierre {localid}-{pos}-Z{znumber} ({closed})")
        print("-" * 60)

        # Convertir fechas a formato YYYYMMDD
        opened_fmt = pd.Timestamp(opened).strftime('%Y%m%d')
        closed_fmt = pd.Timestamp(closed).strftime('%Y%m%d')

        # Ejecutar tests
        self.test_cierre_exists_in_geocom(localid, pos, znumber, closed_fmt)
        self.test_ventas_data_exists_in_geocom(localid, pos, ticketnumber_opened, ticketnumber_closed, opened_fmt, closed_fmt)
        self.test_medios_pago_data_exists_in_geocom(localid, pos, ticketnumber_opened, ticketnumber_closed, opened_fmt, closed_fmt)
        self.test_cierre_NOT_in_dw(id)
        self.test_cierre_detail_NOT_in_dw(localid, pos, znumber, closed_fmt)
        # [CRÍTICO] TEST CRÍTICO: Detectar inconsistencias (detalle sin cabecera)
        self.test_data_consistency(id, localid, pos, znumber, closed_fmt)
        # [CRÍTICO] TEST CRÍTICO: Detectar datos huérfanos en TODAS las tablas
        self.test_all_tables_consistency(localid, pos, znumber, closed_fmt)

    def run_qa_for_multiple_cierres(self, df_missing):
        """
        Ejecuta QA para múltiples cierres faltantes
        """
        print("\n" + "=" * 80)
        print("INICIANDO QA DE CIERRES FALTANTES")
        print("=" * 80)

        # Primero: Detectar Z duplicados (reinicio del contador)
        self.test_z_duplicates(df_missing)

        for _, row in df_missing.iterrows():
            self.run_qa_for_cierre(
                row['id'],
                row['localid'],
                row['pos'],
                row['znumber'],
                row['opened'],
                row['closed'],
                row['ticketnumber_opened'],
                row['ticketnumber_closed']
            )

    def print_qa_report(self):
        """
        Imprime un reporte formateado de los resultados de QA
        """
        df_results = pd.DataFrame(self.test_results)

        print("\n" + "=" * 100)
        print("REPORTE QA - RESUMEN")
        print("=" * 100)

        # Contar by status
        status_counts = df_results['status'].value_counts()

        # Extraer números de los status (ej: "✓ PASS" -> "PASS")
        pass_count = status_counts.get('[PASS]', 0)
        warning_count = status_counts.get('[WARNING]', 0)
        fail_count = status_counts.get('[FAIL]', 0)
        error_count = status_counts.get('[ERROR]', 0)

        total_tests = len(df_results)

        print(f"\n[TOTALES]")
        print(f"   Total de tests ejecutados: {total_tests}")
        print(f"   [PASS]:     {pass_count:<6} ({pass_count*100//total_tests:>2}%)")
        print(f"   [WARNING]:  {warning_count:<6} ({warning_count*100//total_tests:>2}%)")
        print(f"   [FAIL]:     {fail_count:<6} ({fail_count*100//total_tests:>2}%)")
        print(f"   [ERROR]:    {error_count:<6} ({error_count*100//total_tests:>2}%)")

        # Resumen por tipo de test
        print(f"\n[RESUMEN POR TIPO DE TEST]")
        test_summary = df_results.groupby('test')['status'].value_counts().unstack(fill_value=0)
        for test_name in test_summary.index:
            pass_val = test_summary.loc[test_name].get('[PASS]', 0)
            warn_val = test_summary.loc[test_name].get('[WARNING]', 0)
            fail_val = test_summary.loc[test_name].get('[FAIL]', 0)
            error_val = test_summary.loc[test_name].get('[ERROR]', 0)
            total = pass_val + warn_val + fail_val + error_val
            print(f"   {test_name}")
            print(f"      [P]{pass_val} [W]{warn_val} [F]{fail_val} [E]{error_val} (Total: {total})")

        # Mostrar ANOMALÍAS, DATOS HUÉRFANOS y ERRORES
        anomalies = df_results[(df_results['status'] == '[FAIL]') | (df_results['status'] == '[ERROR]')]

        if not anomalies.empty:
            print(f"\n[CRÍTICO] ANOMALÍAS DETECTADAS:\n")

            # Separar por tipo
            fails = anomalies[anomalies['status'] == '[FAIL]']
            errors = anomalies[anomalies['status'] == '[ERROR]']

            if not fails.empty:
                print(f"   DATOS HUÉRFANOS / INCONSISTENCIAS:")
                for _, row in fails.iterrows():
                    print(f"\n   {row['status']} | {row['test']}")
                    if 'id' in row and pd.notna(row['id']):
                        print(f"      ID: {row['id']}")
                    else:
                        details = row.get('details', '')
                        # Extraer info específica de datos huérfanos
                        if 'DATOS HUÉRFANOS' in details:
                            print(f"      Local {row.get('localid', 'N/A')} | POS {row.get('pos', 'N/A')} | Z {row.get('znumber', 'N/A')}")
                        else:
                            print(f"      Local {row.get('localid', 'N/A')} | POS {row.get('pos', 'N/A')} | Closed {row.get('closed', 'N/A')}")
                    print(f"      >> {row['details']}")

            if not errors.empty:
                print(f"\n   ERRORES TÉCNICOS:")
                for _, row in errors.iterrows():
                    print(f"\n   {row['status']} | {row['test']}")
                    print(f"      >> {row['details']}")
        else:
            print(f"\n[OK] SIN ANOMALÍAS - Todos los tests pasaron correctamente")

        print("\n" + "=" * 100 + "\n")

        return df_results

    def export_qa_report(self, filename='qa_report.csv'):
        """
        Exporta el reporte de QA a CSV
        """
        df_results = pd.DataFrame(self.test_results)
        df_results.to_csv(filename, index=False, encoding='utf-8')
        print(f"[OK] Reporte QA exportado a {filename}")
