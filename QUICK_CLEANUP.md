# ⚡ Limpieza Rápida de Cierres Faltantes

## 🎯 El Problema

✅ Identificados: **173 cierres faltantes**
⚠️ Encontrados: **6 casos con detalles huérfanos** (cabecera missing, detalles orphan)

## ⏱️ Ejecución Rápida (3 minutos)

### Opción 1: Automática (RECOMENDADO)

```bash
# UN SOLO COMANDO
python run_cleanup_full.py

# Genera automáticamente:
# ✅ anomaly_report.csv
# ✅ cleanup_results.csv
# ✅ missing_cierres_commands_cleaned.sh
```

### Opción 2: Paso a Paso

```bash
# Paso 1: Analizar anomalías
python analyze_anomalies.py
# → Ver: anomaly_report.csv

# Paso 2: Limpiar detalles
python cleanup_orphan_details.py
# → Ver: cleanup_results.csv

# Paso 3: Generar comandos
python process_with_cleanup.py
# → Ver: missing_cierres_commands_cleaned.sh
```

## 📊 Casos a Procesar

Estos 6 cierres tienen detalles huérfanos:

| Local | POS | Fecha | Z | Orphans |
|-------|-----|-------|---|---------|
| 286 | 1 | 20260112 | Z? | 99 |
| 286 | 1 | 20260122 | Z? | 104 |
| 322 | 1 | 20260122 | Z? | 116 |
| 817 | 1 | 20260131 | Z? | 173 |

## 🔧 Qué Hace Cada Paso

### 1️⃣ Análisis (`analyze_anomalies.py`)
```
→ Obtiene znumber de cada cierre
→ Identifica Z anomalamente cercanos (< 5 min)
→ Valida si tiene datos reales
→ Recomienda: PROCESAR / LIMPIAR / SKIP
```

**Output**: `anomaly_report.csv`

### 2️⃣ Limpieza (`cleanup_orphan_details.py`)
```
→ Busca registros de detalle sin cabecera
→ Elimina de 5 tablas:
   - cierres_detalle
   - cierres_precio_producto
   - cierres_medio_pago
   - cierres_depositos
   - cierres_guias_detalle
→ Verifica que se eliminaron
```

**Output**: `cleanup_results.csv`

**Ejemplo**:
```
Local 286 | POS 1 | Closed 20260112 → Eliminados 99 registros
Local 286 | POS 1 | Closed 20260122 → Eliminados 104 registros
Local 322 | POS 1 | Closed 20260122 → Eliminados 116 registros
Local 817 | POS 1 | Closed 20260131 → Eliminados 173 registros
```

### 3️⃣ Generación de Comandos (`process_with_cleanup.py`)
```
→ Lee anomaly_report.csv
→ Extrae casos con FAIL
→ Obtiene znumber para referencia
→ Genera comandos listos:
   python run.py --localid X --pos Y --fecha_ini YYYYMMDD --fecha_fin YYYYMMDD
```

**Output**: `missing_cierres_commands_cleaned.sh`

**Ejemplo**:
```bash
# Local 286 | POS 1 | Z170 | Closed 20260112
python run.py --localid 286 --pos 1 --fecha_ini 20260112 --fecha_fin 20260112

# Local 286 | POS 1 | Z180 | Closed 20260122
python run.py --localid 286 --pos 1 --fecha_ini 20260122 --fecha_fin 20260122
```

## ✅ Después de Ejecutar

```bash
# Revisar resultados
cat anomaly_report.csv
cat cleanup_results.csv

# Revisar comandos (sin ejecutar)
cat missing_cierres_commands_cleaned.sh

# Cuando estés listo (CON APROBACIÓN PROD):
bash missing_cierres_commands_cleaned.sh
```

## 🔍 Validación

Después de ejecutar bash:

```sql
-- Verificar que se crearon cabeceras
SELECT COUNT(*) FROM modelo_ventas_rauco.dbo.cierres_cabecera
WHERE localid IN (286, 322, 817) AND pos = 1
-- Esperado: 4 (o más si hay otros cierres de esos locales)

-- Verificar que hay detalles
SELECT COUNT(*) FROM modelo_ventas_rauco.dbo.cierres_detalle
WHERE localid IN (286, 322, 817) AND pos = 1
-- Esperado: > 0

-- Verificar que NO hay huérfanos
SELECT COUNT(*) FROM modelo_ventas_rauco.dbo.cierres_detalle
WHERE localid IN (286, 322, 817) AND pos = 1
AND id NOT IN (SELECT id FROM modelo_ventas_rauco.dbo.cierres_cabecera)
-- Esperado: 0
```

## 📁 Archivos Involucrados

**Scripts principales**:
- `analyze_anomalies.py` (165 líneas)
- `cleanup_orphan_details.py` (200 líneas)
- `process_with_cleanup.py` (280 líneas)
- `run_cleanup_full.py` (300 líneas) ← El maestro

**Archivos generados**:
- `anomaly_report.csv` ← Análisis
- `cleanup_results.csv` ← Confirmación de limpieza
- `cleanup_executed.csv` ← Resumen
- `missing_cierres_commands_cleaned.sh` ← Comandos listos

**Documentación**:
- `CLEANUP_WORKFLOW.md` (Detallado)
- `SOLUTION_SUMMARY.md` (Arquitectura)
- `QUICK_CLEANUP.md` (Este archivo)

## 🚀 Flujo Completo Visual

```
┌──────────────────────┐
│  run_cleanup_full.py │  ← TODO EN UNO
└──────────┬───────────┘
           │
     ┌─────▼─────┐
     │ Analizar  │ ─→ anomaly_report.csv
     └─────┬─────┘
           │
     ┌─────▼─────┐
     │ Limpiar   │ ─→ cleanup_results.csv
     └─────┬─────┘
           │
     ┌─────▼──────────┐
     │ Generar Cmds   │ ─→ missing_cierres_commands_cleaned.sh
     └─────┬──────────┘
           │
           │ (Revisar + Aprobación PROD)
           │
     ┌─────▼──────────┐
     │  Ejecutar      │
     │ (bash script)  │
     └────────────────┘
           │
     ┌─────▼──────────┐
     │ Validar (SQL)  │
     └────────────────┘
```

## ⚡ TL;DR (Demasiado Largo; No Leí)

```bash
# 1. Ejecutar análisis + limpieza + generación
python run_cleanup_full.py

# 2. Revisar comandos
cat missing_cierres_commands_cleaned.sh

# 3. Con aprobación PROD
bash missing_cierres_commands_cleaned.sh

# 4. Validar
# (ejecutar queries SQL arriba)
```

✅ **Done!**

---

## 🆘 Troubleshooting

**P: El análisis dice que no hay datos (SKIP)**
R: Revisar en geocom si realmente hay ventas ese día

**P: La limpieza falla**
R: Verificar permisos en DW, intentar limpiar uno por uno

**P: Los comandos no se ejecutan**
R: Verificar conexión a databases, revisar logs en main.py

**P: ¿Puedo ejecutar en DEV primero?**
R: Sí, todos los scripts funcionan igual

---

**Estado**: 🟢 Listo para usar
**Última actualización**: 2026-03-16
