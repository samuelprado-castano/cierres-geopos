from prefect import flow
import subprocess
import sys


@flow(name="missing-cierres-check")
def missing_cierres_flow():
    """Reporte de cierres faltantes GeoPOS - DW - 8 AM"""
    result = subprocess.run(
        [sys.executable, "process_missing_cierres.py"],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise Exception(f"Missing cierres fallo con codigo {result.returncode}: {result.stderr}")
    return result.returncode
