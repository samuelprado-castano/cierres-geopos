# run.py
import sys
import os
import argparse
from datetime import datetime
from src.main import procesar_cierres
# from src.main_qa import procesar_cierres_excel
# from src.vista_qa import procesar_vista_qa

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def parse_arguments():
    parser = argparse.ArgumentParser(description='Ejecutar ETL con destino y tipo de ejecución.')
    parser.add_argument('--modulos', nargs='+', required=True, help='Lista de módulos a ejecutar')
    parser.add_argument('--localid', required=False, default=None, help='Número de local')
    parser.add_argument('--pos', required=False, default=None, help='Número de la caja (1/2/3 o None)')
    parser.add_argument('--z', nargs='+', type=int, default=None, help='Número(s) de cierre Z a procesar. IMPORTANTE: Z puede repetirse después de reinicios del contador.')
    parser.add_argument('--fecha_ini', required=False, default=None, help='Fecha cierre inicial YYYYMMDD (opcional para desambiguar si Z se reinició)')
    parser.add_argument('--fecha_fin', required=False, default=None, help='Fecha cierre final YYYYMMDD (opcional para desambiguar si Z se reinició)')
    parser.add_argument('--dry-run', action='store_true', help='Ejecuta sin escribir en DB (solo lectura)')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()

    # Si es dry-run, permite cualquier combinación (para testing)
    if not args.dry_run:
        # Validar que se especifique --z o --fecha_ini con --fecha_fin
        if not args.z and not (args.fecha_ini and args.fecha_fin):
            import sys
            parser = argparse.ArgumentParser()
            parser.error("Se debe especificar --z o ambos --fecha_ini y --fecha_fin")

        # En modo Z, validar que localid y pos estén definidos
        if args.z:
            if args.localid == "None" or args.pos == "None":
                import sys
                parser = argparse.ArgumentParser()
                parser.error("En modo --z, --localid y --pos son obligatorios (no pueden ser 'None')")

    # Obtener fecha actual en formato YYYYMMDD
    fecha_actual = datetime.now().strftime('%Y%m%d')

    # Default: si no se especifica localid/pos, usar None (para dry-run)
    localid = args.localid if args.localid else None
    pos = args.pos if args.pos else None

    config = {
        "modulos": args.modulos,
        "localid": None if localid == "None" else (int(localid) if localid else None),
        "pos": None if pos == "None" else (int(pos) if pos else None),
        "z": args.z,
        "fecha_ini": args.fecha_ini if args.fecha_ini else fecha_actual,
        "fecha_fin": args.fecha_fin if args.fecha_fin else fecha_actual,
        "iva_rate": 0.19,
        "dry_run": args.dry_run
    }

    # Ejecutar procesamiento
    procesar_cierres(config)
