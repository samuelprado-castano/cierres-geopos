from prefect import flow
import subprocess
import sys


@flow(name="etl-cierres-geopos")
def etl_cierres_flow():
    """ETL diario de cierres GeoPOS a DW - 11 PM"""
    result = subprocess.run(
        [sys.executable, "run.py", "--modulos", "REDONDEOS", "MEDIOS_PAGO", "VENTAS", "DEPOSITOS", "GUIAS"],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise Exception(f"ETL fallo con codigo {result.returncode}: {result.stderr}")
    return result.returncode
