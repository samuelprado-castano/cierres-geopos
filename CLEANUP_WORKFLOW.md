# Flujo de Limpieza de Cierres Faltantes

## Problema Identificado

Al ejecutar QA en 173 cierres faltantes, se encontraron **6 casos con FAILs**:

| Local | POS | Closed | Detalle Huérfano | Znumber |
|-------|-----|--------|------------------|---------|
| 286 | 1 | 20260112 | 99 registros | Z? |
| 286 | 1 | 20260122 | 104 registros | Z? |
| 322 | 1 | 20260122 | 116 registros | Z? |
| 817 | 1 | 20260131 | 173 registros | Z? |

**Causa**: Cierres parciales donde la cabecera NO está en DW, pero los detalles SÍ.

## Solución: DELETE + INSERT

El script `main.py` usa `if_exists='append'` (solo INSERT, nunca DELETE).

### Flujo Completo:

```
┌─────────────────────────────────────────────────┐
│ 1. ANALIZAR ANOMALÍAS POR Z                     │
│    analyze_anomalies.py                         │
│    ├─ Obtiene znumber para cada cierre          │
│    ├─ Identifica Z anomalamente cercanos        │
│    └─ Valida si el cierre tiene datos reales    │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│ 2. LIMPIAR DETALLES HUÉRFANOS                   │
│    cleanup_orphan_details.py                    │
│    ├─ Busca registros de detalle sin cabecera   │
│    ├─ Elimina:                                  │
│    │  - cierres_detalle                         │
│    │  - cierres_precio_producto                 │
│    │  - cierres_medio_pago                      │
│    │  - cierres_depositos                       │
│    │  - cierres_guias_detalle                   │
│    └─ Verifica que se eliminaron                │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│ 3. GENERAR COMANDOS LIMPIOS                     │
│    process_with_cleanup.py                      │
│    ├─ Basados en Z (más preciso)                │
│    ├─ Comando original con closed               │
│    └─ Crea missing_cierres_commands_cleaned.sh  │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│ 4. EJECUTAR CARGA                               │
│    bash missing_cierres_commands_cleaned.sh     │
│    ├─ DELETE ya ocurrió                         │
│    └─ INSERT será nuevo (limpio)                │
└─────────────────────────────────────────────────┘
```

## Ejecución Paso a Paso

### Paso 1: Analizar Anomalías

```bash
python analyze_anomalies.py
```

**Salida esperada**: `anomaly_report.csv`

Contenido: Para cada caso con FAIL, muestra:
- Secuencia de Z antes/después
- Minutos entre cierres
- Datos válidos en geocom
- Recomendación de acción

**Interpretación**:
- `VALID`: Tiene datos reales → procesar normalmente
- `SUSPICIOUS`: No tiene datos → revisar manualmente
- `SKIP`: Z anomalamente cercano + sin datos → saltar
- `LIMPIAR`: Tiene datos pero detalles huérfanos → limpiar antes

---

### Paso 2: Limpiar Detalles Huérfanos

Opción A: Limpiar todos los FAILs conocidos
```bash
python cleanup_orphan_details.py
```

Opción B: Limpiar uno específico
```bash
python cleanup_orphan_details.py 286 1 20260112
python cleanup_orphan_details.py 817 1 20260131
```

**Salida esperada**: `cleanup_results.csv`

Contenido para cada caso:
- `status`: SUCCESS / ERROR / OK (si no hay registros)
- `deleted`: Cantidad de registros eliminados

**Verificación**:
```bash
# Antes de limpiar (debe mostrar registros)
SELECT COUNT(*) FROM modelo_ventas_rauco.dbo.cierres_detalle
WHERE localid = 286 AND pos = 1 AND CAST(CONVERT(VARCHAR, closed, 112) AS INT) = 20260112

# Después de limpiar (debe mostrar 0)
```

---

### Paso 3: Generar Comandos Limpios

```bash
python process_with_cleanup.py
```

**Salida esperada**:
- `cleanup_executed.csv` (confirmación de limpieza)
- `missing_cierres_commands_cleaned.sh` (comandos listos)

**Contenido de comandos**:
```bash
# Local 286 | POS 1 | Z? | Closed 20260112
python run.py --localid 286 --pos 1 --fecha_ini 20260112 --fecha_fin 20260112

# Local 286 | POS 1 | Z? | Closed 20260122
python run.py --localid 286 --pos 1 --fecha_ini 20260122 --fecha_fin 20260122

# ... más comandos ...
```

---

### Paso 4: Ejecutar Comandos Limpios

```bash
# Opción 1: Ejecutar todos
bash missing_cierres_commands_cleaned.sh

# Opción 2: Ejecutar manualmente por caso
python run.py --localid 286 --pos 1 --fecha_ini 20260112 --fecha_fin 20260112
```

**Monitoreo durante ejecución**:
```bash
# Ver logs en tiempo real
tail -f logs/processing.log

# Contar registros cargados
SELECT COUNT(*) FROM modelo_ventas_rauco.dbo.cierres_detalle
WHERE localid = 286 AND pos = 1
```

---

## Análisis por Z (znumber)

El campo `z` (znumber) es preferible a `closed` porque:

1. **Secuencia Precisa**: Es el número secuencial de cierre de la caja
   - Z170, Z171, Z172, Z173... en orden

2. **Identifica Anomalías**: Si Z170 y Z171 tienen solo 2 minutos entre ellos
   - Normal: 8 horas entre Z → Z es válido
   - Anomalía: 2 minutos entre Z → probablemente error de operador o reintento fallido

3. **Reproducibilidad**: Permite identificar exactamente qué cierre se necesita
   - Por fecha (closed): ambiguo si hay múltiples cierres en la misma fecha
   - Por Z: único identificador

### Nomenclatura en Diferentes Tablas

```sql
-- En geocom.totals (origen)
SELECT znumber FROM totals

-- En DW.cierres_detalle (destino)
SELECT z FROM cierres_detalle

-- En DW.cierres_cabecera (destino)
SELECT z FROM cierres_cabecera
```

**Nota**: Nombre cambia (`znumber` vs `z`) pero son el mismo dato.

---

## Validación Final

Después de ejecutar los comandos:

```sql
-- 1. Verificar que las cabeceras se crearon
SELECT COUNT(*) as cabeceras
FROM modelo_ventas_rauco.dbo.cierres_cabecera
WHERE localid IN (286, 322, 817)
AND pos = 1

-- 2. Verificar que los detalles se crearon
SELECT COUNT(*) as detalles
FROM modelo_ventas_rauco.dbo.cierres_detalle
WHERE localid IN (286, 322, 817)
AND pos = 1

-- 3. Verificar correspondencia cabecera ↔ detalle
SELECT
    cc.localid,
    cc.pos,
    cc.z,
    COUNT(DISTINCT cd.id) as count_detalles
FROM modelo_ventas_rauco.dbo.cierres_cabecera cc
LEFT JOIN modelo_ventas_rauco.dbo.cierres_detalle cd
    ON cc.id = cd.id
WHERE cc.localid IN (286, 322, 817)
GROUP BY cc.localid, cc.pos, cc.z
```

---

## Casos Especiales

### Si un cierre sigue sin tener datos después de limpiar

Significa que realmente no tiene datos en geocom. Opciones:

1. **Revisar manualmente en geocom**: ¿Hay ventas para ese día?
   ```sql
   SELECT COUNT(*) FROM geocom.dbo.tickets
   WHERE localid = 286 AND pos = 1
   AND CAST(CONVERT(VARCHAR, opendate, 112) AS INT) BETWEEN 20260111 AND 20260112
   ```

2. **Si no hay datos**: El cierre no debe procesarse (es válido que no exista)

3. **Si hay datos**: El problema es más profundo, revisar logs de main.py

### Si la limpieza falla

```bash
# Verificar permisos en DW
SELECT USER

# Intentar limpieza manual
DELETE FROM modelo_ventas_rauco.dbo.cierres_detalle
WHERE localid = 286 AND pos = 1
AND CAST(CONVERT(VARCHAR, closed, 112) AS INT) = 20260112
```

---

## Resumen Rápido

```bash
# 1. Analizar
python analyze_anomalies.py

# 2. Limpiar
python cleanup_orphan_details.py

# 3. Generar y Ejecutar
python process_with_cleanup.py
bash missing_cierres_commands_cleaned.sh

# 4. Validar
# (Ejecutar queries SQL de validación final)
```

✅ **Listo para PROD cuando se obtenga aprobación**
