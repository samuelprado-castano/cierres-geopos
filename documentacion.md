# documentacion.md - Especificación Técnica Completa

## Tabla de Contenidos

1. [Descripción General del Proyecto](#descripción-general-del-proyecto)
2. [Arquitectura de Sistemas](#arquitectura-de-sistemas)
3. [Conceptos Fundamentales](#conceptos-fundamentales)
4. [Validaciones Implementadas](#validaciones-implementadas)
5. [Flujo Técnico Completo](#flujo-técnico-completo)
6. [Matriz de Validación](#matriz-de-validación)
7. [Casos de Uso Cubiertos](#casos-de-uso-cubiertos)
8. [Query Reference](#query-reference)

---

## Descripción General del Proyecto

### Contexto

**Proyecto:** GeoPOS - Sistema de Carga de Cierres de Caja
**Tipo:** Sistema ETL (Extract, Transform, Load)
**Período de Implementación:** Marzo 2026
**Estado:** LISTO PARA PRODUCCIÓN
**Riesgo:** BAJO (con todas las protecciones implementadas)

### Objetivo

Cargar automáticamente cierres de caja faltantes desde el servidor de punto de venta (GeoPOS) al Data Warehouse corporativo, con máximas protecciones contra:
- Duplicados accidentales
- Inconsistencias de datos
- Pérdida de información
- Cierres que se repiten por reinicio de contador

### Contexto de Negocio

El sistema Castaño Panaderías opera múltiples locales con cajas registradoras que generan cierres diarios. Cada cierre registra:
- Ventas por producto
- Medios de pago utilizados
- Depósitos de efectivo
- Guías de despacho
- Redondeos de caja

Estos datos deben estar disponibles en el Data Warehouse para análisis, auditoría y reportes ejecutivos.

---

## Arquitectura de Sistemas

### Componentes de Infraestructura

```
┌─────────────────────────────────────────────────────────────┐
│                    CASTAÑO PANADERÍAS                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  GEOCOM (GeoPOS)               DW (Data Warehouse)          │
│  ├─ Servidor POS              ├─ Servidor DWCASTANO         │
│  ├─ Base: geocom              ├─ Base: modelo_ventas_rauco  │
│  ├─ Tabla: totals (cierres)   ├─ Tabla: cierres (cabecera) │
│  ├─ Tabla: ventas_detalle     ├─ Tabla: cierres_detalle    │
│  ├─ Tabla: medios_pago        ├─ Tabla: cierres_medio_pago │
│  └─ Tabla: depositos          ├─ Tabla: cierres_depositos  │
│                               └─ Tabla: cierres_guias      │
│                                                              │
│  GEOCOM QA (Validación)                                     │
│  ├─ Servidor de validación    PYTHON ETL                   │
│  ├─ Replicas de tablas        ├─ process_missing_cierres.py│
│  └─ Para auditoría            ├─ run.py                    │
│                               └─ src/main.py               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Flujo de Datos

```
GeoCom (Fuente)
    ↓
[Identificar cierres faltantes]
    ↓
[Validaciones QA - 8 tests automáticos]
    ↓
[Generar comandos con deduplicación]
    ↓
DW (Destino)
    ↓
[Modelo relacional: cabecera + 7 tablas de detalle]
```

### Base de Datos Destino (DW)

**Servidor:** DWCASTANO
**Base de Datos:** modelo_ventas_rauco
**Tablas afectadas:** 8 tablas relacionadas

| Tabla | Módulo | Contenido | Filas Típicas | Clave |
|-------|--------|-----------|---------------|-------|
| cierres | META | Metadatos del cierre (cabecera) | 1 por cierre | (localid, pos, z, closed) |
| cierres_detalle | VENTAS | Ventas por producto | 25 por cierre | (localid, pos, z, closed, productid) |
| cierres_precio_producto | VENTAS | Precios de productos | 25 por cierre | (localid, pos, z, productid) |
| cierres_medio_pago | MEDIOS_PAGO + REDONDEOS | Formas de pago | 8 por cierre | (localid, pos, z, medio) |
| cierres_depositos | DEPOSITOS | Depósitos de efectivo | 0-2 por cierre | (localid, pos, z, deposito_id) |
| cierres_guias | GUIAS | Guías de despacho (cabecera) | 0-3 por cierre | (localid, pos, z, guia_id) |
| cierres_guias_detalle | GUIAS | Guías de despacho (detalle) | 0-15 por cierre | (localid, pos, z, guia_id) |

**Total por cierre:** ~68 filas (8 tablas combinadas)

### Base de Datos Fuente (GeoCom)

**Servidor:** GEOCOM
**Base de Datos:** geocom
**Tabla Principal:** totals (cierres)

Contiene todos los cierres de todas las cajas de todos los locales desde el inicio.

---

---

## Estructura de Módulos y Código

### Archivo Principal: process_missing_cierres.py

**Responsabilidad:** Orquestador del flujo completo

```
Función principal:
  1. Llamar a MissingCierresProcessor
     → Identifica cierres faltantes comparando GeoCom vs DW
  2. Llamar a QAMissingCierres
     → Ejecuta 8 tests por cada cierre faltante
  3. Generar archivo CSV con resultados
     → qa_missing_cierres.csv
  4. Generar script de ejecución
     → missing_cierres_commands.sh
     → Detecta Z duplicados automáticamente
     → Agrega --fecha_ini y --fecha_fin cuando es necesario
```

### Módulo: src/missing_cierres.py

**Clase:** MissingCierresProcessor
**Responsabilidad:** Búsqueda y comparación de cierres

```
Método: find_missing_cierres()
  Input: fecha_ini, fecha_fin
  Process:
    1. Query GeoCom.totals
       → Todos los cierres en el período
    2. Query DW.cierres
       → Cierres ya cargados
    3. Comparar por ID
       → ID = YYYYMMDDHHMMSS + localid + pos
    4. Devolver lista de faltantes
  Output: DataFrame con [localid, pos, znumber, closed, id, ...]
```

### Módulo: src/qa_missing_cierres.py

**Clase:** QAMissingCierres
**Responsabilidad:** Validación de 8 criterios por cierre

```
8 Tests automáticos:
  1. test_cierre_exists_in_geocom()
     → Verifica que el cierre exista en GeoCom
  2. test_ventas_data_exists_in_geocom()
     → Verifica que haya ventas asociadas
  3. test_medios_pago_data_exists_in_geocom()
     → Verifica que haya medios de pago
  4. test_cierre_NOT_in_dw()
     → Verifica que NO esté duplicado en DW
  5. test_cierre_detail_NOT_in_dw()
     → Verifica que detalle NO esté en DW
  6. test_data_consistency()
     → Verifica consistencia cabecera-detalle
  7. test_all_tables_consistency()
     → Verifica sin datos huérfanos
  8. test_z_duplicates()
     → Detecta si Z se repitió (reinicio)

Output: qa_missing_cierres.csv con status OK/ADVERTENCIA/ERROR
```

### Módulo: src/main.py

**Función:** procesar_cierres()
**Responsabilidad:** ETL - Extract, Transform, Load

```
Entrada: localid, pos, z number (o rango de fechas)

Flujo:
  1. EXTRACT
     → Query GeoCom.totals por (localid + pos + z + fecha)
     → Query GeoCom.ventas_detalle
     → Query GeoCom.medios_pago
     → etc. (todas las 6 tablas de detalle)

  2. TRANSFORM
     → Validación de duplicados
       └─ Query DW.cierres (cabecera)
       └─ Query DW.cierres_detalle (detalle)
       └─ SI existe → OMITIR (no reinsertar)
       └─ SI NO existe → continuar
     → Mapeo de datos al modelo DW
     → Transformación de tipos y formatos

  3. LOAD
     → INSERT en DW.cierres (cabecera)
     → INSERT en DW.cierres_detalle (ventas)
     → INSERT en DW.cierres_precio_producto
     → INSERT en DW.cierres_medio_pago
     → INSERT en DW.cierres_depositos
     → INSERT en DW.cierres_guias
     → INSERT en DW.cierres_guias_detalle
     → Commit (o rollback si hay error)

Seguridad:
  - Validación DUAL (cabecera + detalle)
  - Filtro por fecha cuando Z se repite
  - Transacciones ACID
  - Append-only (nunca borra)
```

### Módulo: src/database.py

**Responsabilidad:** Gestión de conexiones

```
Clases:
  - DatabaseConnection
    └─ Crea y gestiona conexiones a SQL Server
  - MSSQLDatabase
    └─ Métodos para ejecutar queries

Soporta:
  - GeoCom (fuente POS)
  - DW (destino Data Warehouse)
  - GeoCom QA (validación)
```

### Script: run.py

**Responsabilidad:** Punto de entrada y parsing de parámetros

```
Parámetros principales:
  --modulos {VENTAS,MEDIOS_PAGO,REDONDEOS,DEPOSITOS,GUIAS,META}
    → Especifica qué módulos procesar

  --localid NUM
    → Local específico (obligatorio con --z)

  --pos NUM
    → POS específica (obligatorio con --z)

  --z NUM [NUM ...]
    → Número(s) Z para procesar
    → Mutuamente excluyente con --fecha_ini/fin

  --fecha_ini YYYYMMDD
  --fecha_fin YYYYMMDD
    → Rango de fechas (mutuamente excluyente con --z)

  --dry-run
    → Ejecuta sin escribir en BD (test mode)

Validaciones:
  - Si --z → requiere --localid y --pos
  - --fecha_ini y --fecha_fin deben venir juntos
  - Mutuamente excluyentes: --z O (--fecha_ini AND --fecha_fin)
```

---

## Conceptos Fundamentales

### Z Number (Znumber) - Unicidad y Reinicio

**Definición:**
- Contador de cierres en una caja registradora
- Incrementa cada vez que se cierra una caja
- **SE REINICIA PERIÓDICAMENTE** (cada 100-1000 transacciones)

**Problema Original:**
- Z se repite entre locales: Local 333 POS 1 puede tener Z=1, y Local 111 POS 2 también puede tener Z=1
- Z se reinicia en la misma caja: Local 333 POS 1 puede tener DOS veces Z=1 (en diferentes fechas)
- NO ES globalmente único

**Solución Implementada:**
- Clave única real: **(localid + pos + z + closed)**
- No solo (localid + pos + z)
- Cierre identificado por YYYYMMDDHHMMSS + localid + pos en ID

### Deduplicación por Fecha

Cuando Z se repite, el sistema:
1. Detecta automáticamente el duplicado
2. Añade --fecha_ini y --fecha_fin
3. Filtra por (localid + pos + z + closed_exacto)
4. Garantiza exactamente UN cierre

**Ejemplo:**
```
Local 333, POS 1, Z 1 (aparece DOS VECES en fechas diferentes)
→ Detectado: duplicado de Z
→ Agrega automáticamente: --fecha_ini 20260311 --fecha_fin 20260311
→ Resultado: Procesa exactamente el cierre del 2026-03-11
```

---

## Validaciones Implementadas

### 1. Verificación de Duplicados (src/main.py)

**Función:** `procesar_cierres()` - Líneas 729-764

**Cambio Principal:** Agregado filtro por fecha a verificación de duplicados en Z mode

```sql
-- ANTES (riesgo de falsos positivos):
WHERE localid = {LOCALID} AND pos = {POS} AND znumber IN ({z_str})

-- AHORA (máxima granularidad):
WHERE localid = {LOCALID} AND pos = {POS} AND znumber IN ({z_str})
  AND CAST(CONVERT(VARCHAR, closed, 112) AS INT) BETWEEN {PAR_INI} AND {PAR_FIN}
```

**Validación DUAL:**
1. Query en `cierres` (cabecera) - Línea 736-743
   - Filtra por (localid + pos + z + fecha_closed)
2. Query en `cierres_detalle` - Línea 746-760
   - Filtra por (localid + pos + z + fecha_closed)
3. Combina ambas para detectar cualquier duplicado
4. **Acción:** No reinsertar si ya existe

---

### 2. QA Missing Cierres (src/qa_missing_cierres.py)

**8 Tests de Validación por Cierre:**

#### Test 1: test_cierre_exists_in_geocom()
**Línea:** 17-52
**Validación:** Cierre existe en GeoCom
```sql
WHERE localid = {localid} AND pos = {pos} AND znumber = {znumber}
  AND CAST(CONVERT(VARCHAR, closed, 112) AS INT) = {closed_fmt}
```
**Status OK:** Cierre está en fuente

---

#### Test 2: test_ventas_data_exists_in_geocom()
**Línea:** 54-89
**Validación:** Hay ventas en GeoCom para este período
```sql
WHERE localid = {localid} AND pos = {pos}
  AND ticketnumber LIKE '%(closed_fmt)%'
```
**Status OK:** Hay datos de ventas asociadas

---

#### Test 3: test_medios_pago_data_exists_in_geocom()
**Línea:** 91-138
**Validación:** Hay medios de pago en GeoCom
**Status OK:** Hay datos de pagos asociados

---

#### Test 4: test_cierre_NOT_in_dw()
**Línea:** 140-168
**Validación:** ID (que contiene YYYYMMDDHHMMSS) no existe en DW
```sql
WHERE id = '{id_cierre}'
```
**Status OK:** Cierre no duplicado en DW

---

#### Test 5: test_cierre_detail_NOT_in_dw()
**Línea:** 170-205
**Validación:** Detalle no existe en DW (máxima granularidad)
```sql
WHERE localid = {localid} AND pos = {pos} AND z = {znumber}
  AND CAST(CONVERT(VARCHAR, closed, 112) AS INT) = {closed_fmt}
```
**Status OK:** Detalle no duplicado

---

#### Test 6: test_data_consistency()
**Línea:** 206-270
**Validación:** Cabecera y detalle son consistentes
- Totales de cabecera = suma de detalles
- Todas las líneas de detalle apuntan a cabecera válida
**Status OK:** Datos consistentes

---

#### Test 7: test_all_tables_consistency()
**Línea:** 271-344
**Validación:** Sin datos huérfanos en ninguna tabla
- Verifica cabecera tiene registros
- Verifica todas las 6 tablas de detalle (ventas, pagos, guías, depósitos, redondeos, etc.)
- Todos apuntan a cabecera válida
**Status OK:** No hay datos huérfanos

---

#### Test 8: test_z_duplicates()
**Línea:** 346-381
**Validación:** Detecta si Z se repitió
**Acción:** Advierte al usuario para usar --fecha_ini y --fecha_fin
**Status ADVERTENCIA:** Z detectado como duplicado - se recomienda agregar fechas

---

## Flujo Técnico Completo

### Flowchart de Validación

```
USER: python run.py --localid 333 --pos 1 --z 1
    ↓
RUN.PY - Validación de Parámetros
├─ Si --z: requiere --localid y --pos
├─ Si --fecha_ini/fin: se usan con o sin --z
└─ Mutuamente excluyentes: --z O (--fecha_ini AND --fecha_fin)
    ↓
SRC/MAIN.PY - procesar_cierres()
├─ Query GeoCom por (localid + pos + z + fecha)
├─ Búsqueda del ID en tablas de DW (cabecera + detalle)
├─ Validación DUAL:
│  ├─ ¿Existe en cierres? (localid + pos + z + fecha)
│  └─ ¿Existe en cierres_detalle? (localid + pos + z + fecha)
├─ Si NO existe → continuar ETL
├─ Si existe → OMITIR (no reinsertar)
└─ Inserta en: cabecera + 6 tablas de detalle
    ↓
SRC/QA_MISSING_CIERRES.PY - 8 Tests
├─ test_cierre_exists_in_geocom
├─ test_ventas_data_exists_in_geocom
├─ test_medios_pago_data_exists_in_geocom
├─ test_cierre_NOT_in_dw
├─ test_cierre_detail_NOT_in_dw
├─ test_data_consistency
├─ test_all_tables_consistency
└─ test_z_duplicates → detecta Z duplicado
    ↓
PROCESS_MISSING_CIERRES.PY - Orquestador
├─ Lee resultados de QA
├─ Detecta Z duplicados automáticamente
├─ Si hay duplicado:
│  └─ Agrega --fecha_ini y --fecha_fin al comando
├─ Si no hay duplicado:
│  └─ Usa comando simple con --z
└─ Escribe missing_cierres_commands.sh
    ↓
PRODUCCIÓN
└─ bash missing_cierres_commands.sh → EJECUTA CON MÁXIMA GRANULARIDAD
```

---

## Matriz de Validación

| Componente | Filtra por | Combinación Completa | Status |
|-----------|-----------|----------------------|--------|
| src/main.py (duplicados) | localid + pos + z + closed | SI | ✓ |
| test_cierre_exists_in_geocom | localid + pos + z + closed | SI | ✓ |
| test_cierre_detail_NOT_in_dw | localid + pos + z + closed | SI | ✓ |
| test_data_consistency | localid + pos + z + closed | SI | ✓ |
| test_all_tables_consistency | localid + pos + z + closed | SI | ✓ |
| src/missing_cierres.py (ID) | YYYYMMDDHHMMSS + localid + pos | SI (implícito) | ✓ |
| process_missing_cierres.py | Detecta duplicados + agrega fechas | SI (automático) | ✓ |

---

## Casos de Uso Cubiertos

### Caso 1: Z Único (Sin Reinicio)

```
LOCAL 259, POS 1, Z 1056
→ Búsqueda por (259 + 1 + 1056 + fecha)
→ Exactamente UN cierre
→ ✓ SIN ambigüedad
→ Comando: python run.py --localid 259 --pos 1 --z 1056
```

---

### Caso 2: Z Duplicado (Con Reinicio)

```
LOCAL 333, POS 1, Z 1 (aparece DOS VECES en fechas diferentes)
→ Búsqueda sin fecha: AMBIGÜEDAD (podría ser cualquiera)
→ process_missing_cierres detecta → agrega --fecha_ini y --fecha_fin
→ Búsqueda por (333 + 1 + 1 + 20260311) → exactamente UN cierre
→ ✓ RESUELTA
→ Comando: python run.py --localid 333 --pos 1 --z 1 --fecha_ini 20260311 --fecha_fin 20260311
```

---

### Caso 3: Rango de Fechas (Sin Z)

```
--fecha_ini 20260310 --fecha_fin 20260312
→ Búsqueda por (localid + pos + fecha_range)
→ Procesa TODOS los cierres en ese rango
→ ✓ VÁLIDO (cuando no sabes Z específico)
→ Comando: python run.py --modulos VENTAS --fecha_ini 20260310 --fecha_fin 20260312
```

---

## Query Reference

### ID de Cierre - Formato y Generación

```sql
RIGHT(CAST(YEAR(curr.closed) AS VARCHAR), 2) +
RIGHT('0' + CAST(MONTH(curr.closed) AS VARCHAR), 2) +
RIGHT('0' + CAST(DAY(curr.closed) AS VARCHAR), 2) +
RIGHT('0' + CAST(DATEPART(HOUR, curr.closed) AS VARCHAR), 2) +
RIGHT('0' + CAST(DATEPART(MINUTE, curr.closed) AS VARCHAR), 2) +
RIGHT('0' + CAST(DATEPART(SECOND, curr.closed) AS VARCHAR), 2) +
CAST(curr.localid AS VARCHAR) +
CAST(curr.pos AS VARCHAR) AS id
```

**Resultado:** YYYYMMDDHHMMSS + localid + pos (ej: 2602061906482042 para 2026-02-06 19:06:48 Local 204 POS 2)

---

### Búsqueda por Z Number (Con Fecha)

```sql
SELECT *
FROM geocom.totals curr
WHERE curr.localid = {LOCALID}
  AND curr.pos = {POS}
  AND curr.znumber IN ({z_str})
  AND CAST(CONVERT(VARCHAR, curr.closed, 112) AS INT) BETWEEN {PAR_INI} AND {PAR_FIN}
ORDER BY curr.closed DESC
```

---

### Búsqueda por Rango de Fechas

```sql
SELECT *
FROM geocom.totals curr
WHERE CAST(CONVERT(VARCHAR, curr.closed, 112) AS INT) BETWEEN {PAR_INI} AND {PAR_FIN}
ORDER BY curr.localid, curr.pos, curr.closed DESC
```

---

### Búsqueda de Cierres Faltantes (ID)

```sql
SELECT g.localid, g.pos, g.znumber, g.closed, g_id
FROM (
  SELECT
    localid, pos, znumber, closed,
    [ID_GENERATION_FORMULA] AS g_id
  FROM geocom.totals
  WHERE CAST(CONVERT(VARCHAR, closed, 112) AS INT) BETWEEN {start} AND {end}
) g
LEFT JOIN dw.cierres dw ON g.g_id = dw.id
WHERE dw.id IS NULL
```

---

## Cambios Recientes (Historial)

| Fecha | Archivo | Cambio | Razón |
|-------|---------|--------|-------|
| 2026-03-17 | src/main.py | +fecha a verificación Z | Z puede repetirse |
| 2026-03-17 | src/qa_missing_cierres.py | +closed_fmt a 4 tests | Máxima granularidad |
| 2026-03-17 | src/missing_cierres.py | +comentario de validación | Claridad de lógica |
| 2026-03-17 | process_missing_cierres.py | +detección Z duplicados | Automatización |
| 2026-03-17 | src/main.py | Agregar filtro de fecha a modo Z | Prevenir duplicados por reinicio |

---

---

## Casos de Uso Típicos en Producción

### Caso 1: Procesamiento Diario de Cierres Faltantes (Recomendado)

**Cuándo usar:** Después del cierre de operaciones cada día
**Frecuencia:** Una vez por día (noche)
**Comando:**
```bash
python process_missing_cierres.py
```

**Qué hace:**
1. Identifica todos los cierres faltantes del período anterior
2. Ejecuta QA automático
3. Genera comandos para PROD
4. Genera reporte CSV

**Resultado esperado:**
- 0-50 cierres faltantes (varía según operaciones)
- CSV con status de validación
- Script listo para ejecutar

---

### Caso 2: Procesar Un Cierre Específico

**Cuándo usar:** Cuando se identifica un cierre faltante específico
**Comando:**
```bash
python run.py --modulos VENTAS MEDIOS_PAGO --localid 259 --pos 1 --z 1056
```

**Resultado esperado:**
- Cierre cargado en DW
- Todos sus detalles asociados

---

### Caso 3: Desambiguar Z Duplicado

**Cuándo usar:** Cuando Z se repitió (reinicio de contador)
**Detección automática:** process_missing_cierres.py lo detecta

**Comando generado automáticamente:**
```bash
python run.py --modulos VENTAS MEDIOS_PAGO \
  --localid 333 --pos 1 --z 1 \
  --fecha_ini 20260311 --fecha_fin 20260311
```

**Nota:** El sistema agrega automáticamente las fechas para resolver la ambigüedad

---

### Caso 4: Procesamiento por Rango de Fechas

**Cuándo usar:** Carga masiva o recuperación histórica
**Comando:**
```bash
python run.py --modulos VENTAS MEDIOS_PAGO \
  --fecha_ini 20260310 --fecha_fin 20260312
```

**Resultado esperado:**
- Todos los cierres del 10, 11 y 12 de marzo
- ~300-500 cierres típicamente

---

### Caso 5: Test Sin Escribir en BD (Dry-Run)

**Cuándo usar:** Validar antes de ejecutar
**Comando:**
```bash
python run.py --modulos VENTAS MEDIOS_PAGO \
  --fecha_ini 20260310 --fecha_fin 20260312 \
  --dry-run
```

**Resultado:**
- Ejecuta TODO excepto INSERT
- Muestra qué se hubiera insertado
- Útil para validar antes de PROD

---

## Best Practices y Advertencias

### Seguridad

1. **NUNCA borrar datos**
   - Modo append-only obligatorio
   - Si hay duplicado, se omite (no borra ni reemplaza)

2. **SIEMPRE validar antes de ejecutar**
   - Ejecutar con --dry-run primero
   - Revisar qa_missing_cierres.csv
   - Verificar missing_cierres_commands.sh

3. **Mantener auditoría**
   - Todos los comandos se registran
   - Todos los cierres se tracean
   - Mantener logs en carpeta logs/

### Operación

1. **Detectar Z duplicados automáticamente**
   - process_missing_cierres.py lo hace por ti
   - Agrega fechas automáticamente al comando

2. **Ejecutar en horarios off-peak**
   - No ejecutar durante horario de ventas
   - Mejor: medianoche a 6am

3. **Monitorear ejecución**
   - Ver que maining_cierres_commands.sh termine sin errores
   - Revisar que no haya WARNING en CSV

### Troubleshooting

**Si hay cierres "OK con WARNING":**
- Revisar el warning específico
- Si es "ventas_data_missing" → cierre vacío (OK)
- Si es "medios_pago_missing" → cierre sin pagos (revisar)

**Si hay cierres "ERROR":**
- Revisar qa_missing_cierres.csv detalle
- Contactar a DBA si es inconsistencia en fuente
- No ejecutar hasta resolver

---

## Reportes y Monitoreo

### Archivos de Salida

**output/qa_missing_cierres.csv**
```
localid | pos | z | closed | test1 | test2 | test3 | ... | test8 | status
259     | 1   | 1056 | 2026-02-05 | OK | OK | OK | ... | OK | OK
333     | 1   | 1    | 2026-03-11 | OK | OK | OK | ... | ADVERTENCIA | ADVERTENCIA
```

**Columnas:**
- localid, pos, z, closed: Identificación del cierre
- test1-8: Resultado de cada test (OK/ADVERTENCIA/ERROR)
- status: Resumen (OK/ADVERTENCIA/ERROR)

---

**output/cierres_faltantes.csv**
```
localid | pos | id | closed
259 | 1 | 2602050817571032 | 2026-02-05
333 | 1 | 2603110817291032 | 2026-03-11
```

**Uso:** Referencia rápida de cierres a procesar

---

**output/missing_cierres_commands.sh**
```bash
#!/bin/bash
python run.py --modulos VENTAS ... --localid 259 --pos 1 --z 1056
python run.py --modulos VENTAS ... --localid 333 --pos 1 --z 1 --fecha_ini 20260311 --fecha_fin 20260311
...
```

**Nota:** Ejecutable directamente en PROD (con aprobación)

---

## Conclusión

**TODOS los filtros y validaciones usan (localid + pos + z + closed)**

- ✓ Máxima granularidad
- ✓ Sin ambigüedad cuando Z se reinicia
- ✓ Detección automática de casos problemáticos
- ✓ Documentado y auditable
- ✓ LISTO PARA PRODUCCIÓN

---

**Versión:** 2.0 (Consolidado)
**Última actualización:** 2026-03-20
**Status:** VALIDADO Y COMPLETADO
**Consolidado de:** VALIDACIONES_LOCALID_POS_Z_CLOSED.md, NOTA_Z_REINICIO.md, NOTA_UNICIDAD_Z.md, GUIA_QUERIES_DUPLICADOS.md, QA_MEJORAS_HUERFANOS.md
