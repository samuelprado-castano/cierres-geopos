# Guía: Queries para Detectar Duplicados por (localid + pos + closed + z)

## Archivo

`QUERIES_DUPLICADOS_LOCALID_POS_CLOSED_Z.sql` - Conjunto completo de queries para auditoría

---

## Uso Rápido

### 1. Ver si hay duplicados en TODAS las tablas

```sql
-- Resumen general: cuál tabla tiene más duplicados
SELECT
    'cierres' as tabla,
    COUNT(*) as total_duplicados
FROM modelo_ventas_rauco.cierres
WHERE (localid, pos, closed, znumber) IN (
    SELECT localid, pos, closed, znumber
    FROM modelo_ventas_rauco.cierres
    GROUP BY localid, pos, closed, znumber
    HAVING COUNT(*) > 1
)
UNION ALL
-- ... (repetir para cada tabla)
```

**Resultado esperado:** 0 duplicados en todas las tablas

---

### 2. Encontrar un cierre específico y sus datos

```sql
DECLARE @localid INT = 259;
DECLARE @pos INT = 1;
DECLARE @closed DATE = '2026-01-02';
DECLARE @z INT = 1056;

-- Ver ese cierre en TODAS las tablas
SELECT 'cierres' as tabla, id, localid, pos, znumber, closed FROM modelo_ventas_rauco.cierres
WHERE localid = @localid AND pos = @pos AND ...
UNION ALL
-- ... (repetir para cada tabla)
```

---

## Queries por Tabla

Cada tabla tiene 3 queries:

### Pattern 1: Contar Duplicados
```sql
SELECT
    localid, pos, closed, z,
    COUNT(*) as cantidad
FROM modelo_ventas_rauco.[tabla]
GROUP BY localid, pos, closed, z
HAVING COUNT(*) > 1
ORDER BY localid, pos, closed DESC;
```
**Resultado:** Lista de (localid, pos, closed, z) que se repiten

---

### Pattern 2: Listar Duplicados Detallados
```sql
SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY localid, pos, closed, z ORDER BY closed DESC) as numero_duplicado
FROM modelo_ventas_rauco.[tabla]
WHERE (localid, pos, closed, z) IN (
    SELECT localid, pos, closed, z
    FROM modelo_ventas_rauco.[tabla]
    GROUP BY localid, pos, closed, z
    HAVING COUNT(*) > 1
)
ORDER BY localid, pos, closed DESC, numero_duplicado;
```
**Resultado:** Todos los registros duplicados con sus datos completos

---

### Pattern 3: Contar Total Duplicados
```sql
SELECT
    COUNT(*) as total_registros_duplicados
FROM modelo_ventas_rauco.[tabla]
WHERE (localid, pos, closed, z) IN (
    SELECT localid, pos, closed, z
    FROM modelo_ventas_rauco.[tabla]
    GROUP BY localid, pos, closed, z
    HAVING COUNT(*) > 1
);
```
**Resultado:** Número total de registros que son parte de duplicados

---

## Tablas Auditadas

| # | Tabla | Descripción |
|---|-------|-------------|
| 1 | cierres | Cabecera principal (1 por cierre) |
| 2 | cierres_detalle | Detalles de ventas por producto |
| 3 | cierres_precio_producto | Precios unitarios de productos |
| 4 | cierres_medio_pago | Formas de pago + redondeos |
| 5 | cierres_depositos | Depósitos de efectivo |
| 6 | cierres_guias | Guías de despacho (cabecera) |
| 7 | cierres_guias_detalle | Guías de despacho (detalle) |

---

## Ejemplos de Uso

### Ejemplo 1: Encontrar Todos los Duplicados en cierres_detalle

```sql
-- Step 1: Contar
SELECT localid, pos, closed, z, COUNT(*) as qty
FROM modelo_ventas_rauco.cierres_detalle
GROUP BY localid, pos, closed, z
HAVING COUNT(*) > 1
ORDER BY qty DESC;

-- Step 2: Ver detalles completos
SELECT * FROM modelo_ventas_rauco.cierres_detalle
WHERE (localid, pos, closed, z) IN (
    SELECT localid, pos, closed, z
    FROM modelo_ventas_rauco.cierres_detalle
    GROUP BY localid, pos, closed, z
    HAVING COUNT(*) > 1
)
ORDER BY localid, pos, closed DESC;
```

---

### Ejemplo 2: Auditar un Cierre Específico (259-1-20260102-1056)

```sql
-- Ver en cierres
SELECT * FROM modelo_ventas_rauco.cierres
WHERE localid = 259 AND pos = 1 AND znumber = 1056
  AND CAST(CONVERT(VARCHAR, closed, 112) AS INT) = 20260102;

-- Ver en cierres_detalle
SELECT * FROM modelo_ventas_rauco.cierres_detalle
WHERE localid = 259 AND pos = 1 AND z = 1056
  AND CAST(CONVERT(VARCHAR, closed, 112) AS INT) = 20260102;

-- Repetir para cada tabla...
```

---

### Ejemplo 3: Buscar Duplicados en Últimas 7 Días

```sql
DECLARE @dias INT = 7;
DECLARE @fecha_ini DATE = DATEADD(DAY, -@dias, CAST(GETDATE() AS DATE));

SELECT
    localid, pos, closed, z,
    COUNT(*) as cantidad
FROM modelo_ventas_rauco.cierres_detalle
WHERE closed >= @fecha_ini
GROUP BY localid, pos, closed, z
HAVING COUNT(*) > 1
ORDER BY closed DESC;
```

---

### Ejemplo 4: Encontrar Cierre con Mayor Duplicación

```sql
-- Cuál cierre tiene más duplicados
SELECT TOP 1
    localid, pos, closed, z,
    COUNT(*) as total_duplicados
FROM modelo_ventas_rauco.cierres_detalle
GROUP BY localid, pos, closed, z
HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC;
```

---

## Interpretación de Resultados

### ✓ CORRECTO
- 0 filas retornadas en "Contar Duplicados"
- Cada combinación (localid + pos + closed + z) aparece 1 vez solamente

### ❌ PROBLEMA
- Se retornan filas con COUNT(*) > 1
- Significa que hay reinserciones accidentales
- Necesita investigación y cleanup

---

## Cleanup (Si hay duplicados)

### Opción 1: Eliminar Duplicados (Mantener 1 registro)

```sql
-- Para cierres_detalle (ejemplo)
WITH duplicados AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY localid, pos, closed, z ORDER BY id DESC) as rn
    FROM modelo_ventas_rauco.cierres_detalle
    WHERE (localid, pos, closed, z) IN (
        SELECT localid, pos, closed, z
        FROM modelo_ventas_rauco.cierres_detalle
        GROUP BY localid, pos, closed, z
        HAVING COUNT(*) > 1
    )
)
DELETE FROM duplicados WHERE rn > 1;
```

### Opción 2: Backup antes de limpiar

```sql
-- Crear tabla de backup
SELECT * INTO modelo_ventas_rauco.cierres_detalle_backup
FROM modelo_ventas_rauco.cierres_detalle
WHERE (localid, pos, closed, z) IN (
    SELECT localid, pos, closed, z
    FROM modelo_ventas_rauco.cierres_detalle
    GROUP BY localid, pos, closed, z
    HAVING COUNT(*) > 1
);

-- Luego eliminar duplicados
WITH duplicados AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY localid, pos, closed, z ORDER BY id DESC) as rn
    FROM modelo_ventas_rauco.cierres_detalle
    WHERE (localid, pos, closed, z) IN (
        SELECT localid, pos, closed, z
        FROM modelo_ventas_rauco.cierres_detalle
        GROUP BY localid, pos, closed, z
        HAVING COUNT(*) > 1
    )
)
DELETE FROM duplicados WHERE rn > 1;
```

---

## Monitoreo Post-Ejecución

Después de ejecutar `process_missing_cierres.py` en PROD:

```sql
-- 1. Verificar que NO hay duplicados
SELECT 'cierres' as tabla, COUNT(*) as total_duplicados
FROM modelo_ventas_rauco.cierres
WHERE (localid, pos, closed, znumber) IN (
    SELECT localid, pos, closed, znumber
    FROM modelo_ventas_rauco.cierres
    GROUP BY localid, pos, closed, znumber
    HAVING COUNT(*) > 1
);

-- 2. Ver últimos cierres cargados
SELECT TOP 10 *
FROM modelo_ventas_rauco.cierres
ORDER BY closed DESC;

-- 3. Contar registros por tabla
SELECT 'cierres' as tabla, COUNT(*) as total
FROM modelo_ventas_rauco.cierres
UNION ALL
SELECT 'cierres_detalle', COUNT(*)
FROM modelo_ventas_rauco.cierres_detalle
-- ... repetir para cada tabla
```

---

## Parámetros de las Queries

### Columnas Clave

**cierres:**
- `localid` - Número de local
- `pos` - Número de caja
- `closed` - Timestamp del cierre
- `znumber` - Contador Z

**Demás tablas:**
- `localid` - Número de local
- `pos` - Número de caja
- `closed` - Timestamp del cierre
- `z` - Contador Z (nota: "z" en lugar de "znumber")
- `id` - ID del cierre (YYYYMMDDHHMMSS + localid + pos)

---

## Checklist de Auditoría

- [ ] Ejecutar "Resumen general" - confirmar 0 duplicados
- [ ] Auditar tabla `cierres` - no hay duplicados
- [ ] Auditar tabla `cierres_detalle` - no hay duplicados
- [ ] Auditar tabla `cierres_precio_producto` - no hay duplicados
- [ ] Auditar tabla `cierres_medio_pago` - no hay duplicados
- [ ] Auditar tabla `cierres_depositos` - no hay duplicados
- [ ] Auditar tabla `cierres_guias` - no hay duplicados
- [ ] Auditar tabla `cierres_guias_detalle` - no hay duplicados
- [ ] Verificar último cierre cargado
- [ ] Contar total de registros por tabla
- [ ] Comparar con números esperados

---

## Soporte

Si encuentras duplicados:

1. Ejecutar "Listar Duplicados Detallados" para identificar qué se duplicó
2. Revisar logs de ejecución para ver cuándo ocurrió
3. Ejecutar "Cleanup" para eliminar duplicados
4. Re-ejecutar auditoría para confirmar que se limpió
5. Ajustar lógica en Python si es necesario (comunicar al equipo)

---

**Versión:** 1.0
**Última actualización:** 2026-03-17
**Estado:** LISTO PARA USAR
