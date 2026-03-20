#!/bin/bash
# Script generado automáticamente para procesar cierres faltantes
# Generado: 2026-03-18 11:54:32
# Modo: Ejecución directa por Z (znumber) - sin fechas
# NOTA: Ejecutar solo en PROD después de QA

# Local 127 | POS 2 | Z 2466 | Closed 20260317
python run.py --modulos VENTAS MEDIOS_PAGO REDONDEOS DEPOSITOS GUIAS --localid 127 --pos 2 --z 2466 --fecha_ini 20260317 --fecha_fin 20260317

# Local 272 | POS 1 | Z 194 | Closed 20260317
python run.py --modulos VENTAS MEDIOS_PAGO REDONDEOS DEPOSITOS GUIAS --localid 272 --pos 1 --z 194 --fecha_ini 20260317 --fecha_fin 20260317

