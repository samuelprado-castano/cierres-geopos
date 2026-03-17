-- ====================================================================================================
-- QUERIES PARA DETECTAR DUPLICADOS POR (localid + pos + closed + z)
-- SINTAXIS CORRECTA PARA SQL SERVER (No usa tuplas en IN)
-- ====================================================================================================

-- ====================================================================================================
-- 1. TABLA: cierres (Cabecera Principal)
-- ====================================================================================================

-- Contar duplicados por (localid + pos + closed + znumber)
SELECT
    localid,
    pos,
    closed,
    znumber,
    COUNT(*) as cantidad
FROM modelo_ventas_rauco.cierres
GROUP BY localid, pos, closed, znumber
HAVING COUNT(*) > 1
ORDER BY localid, pos, closed DESC;

-- Listar todos los duplicados con detalles
WITH DuplicadosCTE AS (
    SELECT
        id,
        localid,
        pos,
        opened,
        closed,
        znumber,
        state,
        COUNT(*) OVER (PARTITION BY localid, pos, closed, znumber) as total_ocurrencias,
        ROW_NUMBER() OVER (PARTITION BY localid, pos, closed, znumber ORDER BY closed DESC) as numero_duplicado
    FROM modelo_ventas_rauco.cierres
)
SELECT
    id, localid, pos, opened, closed, znumber, state, numero_duplicado
FROM DuplicadosCTE
WHERE total_ocurrencias > 1
ORDER BY localid, pos, closed DESC, numero_duplicado;

-- Contar total de duplicados
WITH DuplicadosCTE AS (
    SELECT
        COUNT(*) OVER (PARTITION BY localid, pos, closed, znumber) as total_ocurrencias
    FROM modelo_ventas_rauco.cierres
)
SELECT
    COUNT(*) as total_duplicados
FROM DuplicadosCTE
WHERE total_ocurrencias > 1;

---

-- ====================================================================================================
-- 2. TABLA: cierres_detalle (Detalle de Ventas)
-- ====================================================================================================

-- Contar duplicados por (localid + pos + closed + z)
SELECT
    localid,
    pos,
    closed,
    z,
    COUNT(*) as cantidad,
    COUNT(DISTINCT id) as cierres_unicos
FROM modelo_ventas_rauco.cierres_detalle
GROUP BY localid, pos, closed, z
HAVING COUNT(*) > 1
ORDER BY localid, pos, closed DESC;

-- Listar todos los duplicados con detalles
WITH DuplicadosCTE AS (
    SELECT
        id,
        localid,
        pos,
        closed,
        z,
        item,
        description,
        umquantity,
        amount,
        COUNT(*) OVER (PARTITION BY localid, pos, closed, z) as total_ocurrencias,
        ROW_NUMBER() OVER (PARTITION BY localid, pos, closed, z ORDER BY closed DESC) as numero_duplicado
    FROM modelo_ventas_rauco.cierres_detalle
)
SELECT
    id, localid, pos, closed, z, item, description, umquantity, amount, numero_duplicado
FROM DuplicadosCTE
WHERE total_ocurrencias > 1
ORDER BY localid, pos, closed DESC, z, numero_duplicado;

-- Contar registros duplicados
WITH DuplicadosCTE AS (
    SELECT
        COUNT(*) OVER (PARTITION BY localid, pos, closed, z) as total_ocurrencias
    FROM modelo_ventas_rauco.cierres_detalle
)
SELECT
    COUNT(*) as total_registros_duplicados
FROM DuplicadosCTE
WHERE total_ocurrencias > 1;

---

-- ====================================================================================================
-- 3. TABLA: cierres_precio_producto (Precios de Productos)
-- ====================================================================================================

-- Contar duplicados por (localid + pos + closed + z)
SELECT
    localid,
    pos,
    closed,
    z,
    COUNT(*) as cantidad,
    COUNT(DISTINCT id) as cierres_unicos
FROM modelo_ventas_rauco.cierres_precio_producto
GROUP BY localid, pos, closed, z
HAVING COUNT(*) > 1
ORDER BY localid, pos, closed DESC;

-- Listar todos los duplicados con detalles
WITH DuplicadosCTE AS (
    SELECT
        id,
        localid,
        pos,
        closed,
        z,
        item,
        unitamount,
        netunitamount,
        taxunitamount,
        COUNT(*) OVER (PARTITION BY localid, pos, closed, z) as total_ocurrencias,
        ROW_NUMBER() OVER (PARTITION BY localid, pos, closed, z ORDER BY closed DESC) as numero_duplicado
    FROM modelo_ventas_rauco.cierres_precio_producto
)
SELECT
    id, localid, pos, closed, z, item, unitamount, netunitamount, taxunitamount, numero_duplicado
FROM DuplicadosCTE
WHERE total_ocurrencias > 1
ORDER BY localid, pos, closed DESC, z, numero_duplicado;

-- Contar registros duplicados
WITH DuplicadosCTE AS (
    SELECT
        COUNT(*) OVER (PARTITION BY localid, pos, closed, z) as total_ocurrencias
    FROM modelo_ventas_rauco.cierres_precio_producto
)
SELECT
    COUNT(*) as total_registros_duplicados
FROM DuplicadosCTE
WHERE total_ocurrencias > 1;

---

-- ====================================================================================================
-- 4. TABLA: cierres_medio_pago (Formas de Pago + Redondeos)
-- ====================================================================================================

-- Contar duplicados por (localid + pos + closed + z)
SELECT
    localid,
    pos,
    closed,
    z,
    COUNT(*) as cantidad,
    COUNT(DISTINCT id) as cierres_unicos
FROM modelo_ventas_rauco.cierres_medio_pago
GROUP BY localid, pos, closed, z
HAVING COUNT(*) > 1
ORDER BY localid, pos, closed DESC;

-- Listar todos los duplicados con detalles
WITH DuplicadosCTE AS (
    SELECT
        id,
        localid,
        pos,
        closed,
        z,
        paymentid,
        name,
        grossamount,
        taxamount,
        netamount,
        COUNT(*) OVER (PARTITION BY localid, pos, closed, z) as total_ocurrencias,
        ROW_NUMBER() OVER (PARTITION BY localid, pos, closed, z ORDER BY closed DESC) as numero_duplicado
    FROM modelo_ventas_rauco.cierres_medio_pago
)
SELECT
    id, localid, pos, closed, z, paymentid, name, grossamount, taxamount, netamount, numero_duplicado
FROM DuplicadosCTE
WHERE total_ocurrencias > 1
ORDER BY localid, pos, closed DESC, z, numero_duplicado;

-- Contar registros duplicados
WITH DuplicadosCTE AS (
    SELECT
        COUNT(*) OVER (PARTITION BY localid, pos, closed, z) as total_ocurrencias
    FROM modelo_ventas_rauco.cierres_medio_pago
)
SELECT
    COUNT(*) as total_registros_duplicados
FROM DuplicadosCTE
WHERE total_ocurrencias > 1;

---

-- ====================================================================================================
-- 5. TABLA: cierres_depositos (Depósitos de Efectivo)
-- ====================================================================================================

-- Contar duplicados por (localid + pos + closed + z)
SELECT
    localid,
    pos,
    closed,
    z,
    COUNT(*) as cantidad,
    COUNT(DISTINCT id) as cierres_unicos
FROM modelo_ventas_rauco.cierres_depositos
GROUP BY localid, pos, closed, z
HAVING COUNT(*) > 1
ORDER BY localid, pos, closed DESC;

-- Listar todos los duplicados con detalles
WITH DuplicadosCTE AS (
    SELECT
        id,
        localid,
        pos,
        closed,
        z,
        folio,
        type,
        amount,
        COUNT(*) OVER (PARTITION BY localid, pos, closed, z) as total_ocurrencias,
        ROW_NUMBER() OVER (PARTITION BY localid, pos, closed, z ORDER BY closed DESC) as numero_duplicado
    FROM modelo_ventas_rauco.cierres_depositos
)
SELECT
    id, localid, pos, closed, z, folio, type, amount, numero_duplicado
FROM DuplicadosCTE
WHERE total_ocurrencias > 1
ORDER BY localid, pos, closed DESC, z, numero_duplicado;

-- Contar registros duplicados
WITH DuplicadosCTE AS (
    SELECT
        COUNT(*) OVER (PARTITION BY localid, pos, closed, z) as total_ocurrencias
    FROM modelo_ventas_rauco.cierres_depositos
)
SELECT
    COUNT(*) as total_registros_duplicados
FROM DuplicadosCTE
WHERE total_ocurrencias > 1;

---

-- ====================================================================================================
-- 6. TABLA: cierres_guias (Guías de Despacho - Cabecera)
-- ====================================================================================================

-- Contar duplicados por (localid + pos + closed + z)
SELECT
    localid,
    pos,
    closed,
    z,
    COUNT(*) as cantidad,
    COUNT(DISTINCT id) as cierres_unicos
FROM modelo_ventas_rauco.cierres_guias
GROUP BY localid, pos, closed, z
HAVING COUNT(*) > 1
ORDER BY localid, pos, closed DESC;

-- Listar todos los duplicados con detalles
WITH DuplicadosCTE AS (
    SELECT
        id,
        localid,
        pos,
        closed,
        z,
        documentnumber,
        date,
        hour,
        patent,
        sendstate,
        COUNT(*) OVER (PARTITION BY localid, pos, closed, z) as total_ocurrencias,
        ROW_NUMBER() OVER (PARTITION BY localid, pos, closed, z ORDER BY closed DESC) as numero_duplicado
    FROM modelo_ventas_rauco.cierres_guias
)
SELECT
    id, localid, pos, closed, z, documentnumber, date, hour, patent, sendstate, numero_duplicado
FROM DuplicadosCTE
WHERE total_ocurrencias > 1
ORDER BY localid, pos, closed DESC, z, numero_duplicado;

-- Contar registros duplicados
WITH DuplicadosCTE AS (
    SELECT
        COUNT(*) OVER (PARTITION BY localid, pos, closed, z) as total_ocurrencias
    FROM modelo_ventas_rauco.cierres_guias
)
SELECT
    COUNT(*) as total_registros_duplicados
FROM DuplicadosCTE
WHERE total_ocurrencias > 1;

---

-- ====================================================================================================
-- 7. TABLA: cierres_guias_detalle (Guías de Despacho - Detalle)
-- ====================================================================================================

-- Contar duplicados por (localid + pos + closed + z)
SELECT
    localid,
    pos,
    closed,
    z,
    COUNT(*) as cantidad,
    COUNT(DISTINCT id) as cierres_unicos
FROM modelo_ventas_rauco.cierres_guias_detalle
GROUP BY localid, pos, closed, z
HAVING COUNT(*) > 1
ORDER BY localid, pos, closed DESC;

-- Listar todos los duplicados con detalles
WITH DuplicadosCTE AS (
    SELECT
        id,
        localid,
        pos,
        closed,
        z,
        documentnumber,
        item,
        quantity,
        amount,
        COUNT(*) OVER (PARTITION BY localid, pos, closed, z) as total_ocurrencias,
        ROW_NUMBER() OVER (PARTITION BY localid, pos, closed, z ORDER BY closed DESC) as numero_duplicado
    FROM modelo_ventas_rauco.cierres_guias_detalle
)
SELECT
    id, localid, pos, closed, z, documentnumber, item, quantity, amount, numero_duplicado
FROM DuplicadosCTE
WHERE total_ocurrencias > 1
ORDER BY localid, pos, closed DESC, z, numero_duplicado;

-- Contar registros duplicados
WITH DuplicadosCTE AS (
    SELECT
        COUNT(*) OVER (PARTITION BY localid, pos, closed, z) as total_ocurrencias
    FROM modelo_ventas_rauco.cierres_guias_detalle
)
SELECT
    COUNT(*) as total_registros_duplicados
FROM DuplicadosCTE
WHERE total_ocurrencias > 1;

---

-- ====================================================================================================
-- RESUMEN GENERAL: Duplicados en TODAS las tablas
-- ====================================================================================================

WITH AllDuplicates AS (
    SELECT 'cierres' as tabla, COUNT(*) as total_duplicados
    FROM (
        SELECT COUNT(*) OVER (PARTITION BY localid, pos, closed, znumber) as total_ocu
        FROM modelo_ventas_rauco.cierres
    ) x
    WHERE total_ocu > 1

    UNION ALL

    SELECT 'cierres_detalle', COUNT(*)
    FROM (
        SELECT COUNT(*) OVER (PARTITION BY localid, pos, closed, z) as total_ocu
        FROM modelo_ventas_rauco.cierres_detalle
    ) x
    WHERE total_ocu > 1

    UNION ALL

    SELECT 'cierres_precio_producto', COUNT(*)
    FROM (
        SELECT COUNT(*) OVER (PARTITION BY localid, pos, closed, z) as total_ocu
        FROM modelo_ventas_rauco.cierres_precio_producto
    ) x
    WHERE total_ocu > 1

    UNION ALL

    SELECT 'cierres_medio_pago', COUNT(*)
    FROM (
        SELECT COUNT(*) OVER (PARTITION BY localid, pos, closed, z) as total_ocu
        FROM modelo_ventas_rauco.cierres_medio_pago
    ) x
    WHERE total_ocu > 1

    UNION ALL

    SELECT 'cierres_depositos', COUNT(*)
    FROM (
        SELECT COUNT(*) OVER (PARTITION BY localid, pos, closed, z) as total_ocu
        FROM modelo_ventas_rauco.cierres_depositos
    ) x
    WHERE total_ocu > 1

    UNION ALL

    SELECT 'cierres_guias', COUNT(*)
    FROM (
        SELECT COUNT(*) OVER (PARTITION BY localid, pos, closed, z) as total_ocu
        FROM modelo_ventas_rauco.cierres_guias
    ) x
    WHERE total_ocu > 1

    UNION ALL

    SELECT 'cierres_guias_detalle', COUNT(*)
    FROM (
        SELECT COUNT(*) OVER (PARTITION BY localid, pos, closed, z) as total_ocu
        FROM modelo_ventas_rauco.cierres_guias_detalle
    ) x
    WHERE total_ocu > 1
)
SELECT tabla, total_duplicados FROM AllDuplicates
ORDER BY total_duplicados DESC;

---

-- ====================================================================================================
-- AUDITORÍA: Cierre específico en TODAS las tablas
-- ====================================================================================================

DECLARE @localid INT = 259;
DECLARE @pos INT = 1;
DECLARE @closed_date INT = 20260102;  -- YYYYMMDD
DECLARE @z INT = 1056;

-- Cabecera
SELECT 'cierres' as tabla, id, localid, pos, znumber, closed FROM modelo_ventas_rauco.cierres
WHERE localid = @localid AND pos = @pos AND CAST(CONVERT(VARCHAR, closed, 112) AS INT) = @closed_date AND znumber = @z

UNION ALL

-- Detalle
SELECT 'cierres_detalle', id, localid, pos, CAST(z AS VARCHAR), closed FROM modelo_ventas_rauco.cierres_detalle
WHERE localid = @localid AND pos = @pos AND CAST(CONVERT(VARCHAR, closed, 112) AS INT) = @closed_date AND z = @z

UNION ALL

-- Precios
SELECT 'cierres_precio_producto', id, localid, pos, CAST(z AS VARCHAR), closed FROM modelo_ventas_rauco.cierres_precio_producto
WHERE localid = @localid AND pos = @pos AND CAST(CONVERT(VARCHAR, closed, 112) AS INT) = @closed_date AND z = @z

UNION ALL

-- Medios pago
SELECT 'cierres_medio_pago', id, localid, pos, CAST(z AS VARCHAR), closed FROM modelo_ventas_rauco.cierres_medio_pago
WHERE localid = @localid AND pos = @pos AND CAST(CONVERT(VARCHAR, closed, 112) AS INT) = @closed_date AND z = @z

UNION ALL

-- Depósitos
SELECT 'cierres_depositos', id, localid, pos, CAST(z AS VARCHAR), closed FROM modelo_ventas_rauco.cierres_depositos
WHERE localid = @localid AND pos = @pos AND CAST(CONVERT(VARCHAR, closed, 112) AS INT) = @closed_date AND z = @z

UNION ALL

-- Guías
SELECT 'cierres_guias', id, localid, pos, CAST(z AS VARCHAR), closed FROM modelo_ventas_rauco.cierres_guias
WHERE localid = @localid AND pos = @pos AND CAST(CONVERT(VARCHAR, closed, 112) AS INT) = @closed_date AND z = @z

UNION ALL

-- Guías detalle
SELECT 'cierres_guias_detalle', id, localid, pos, CAST(z AS VARCHAR), closed FROM modelo_ventas_rauco.cierres_guias_detalle
WHERE localid = @localid AND pos = @pos AND CAST(CONVERT(VARCHAR, closed, 112) AS INT) = @closed_date AND z = @z;

---

-- ====================================================================================================
-- CONTEO TOTAL DE REGISTROS POR TABLA
-- ====================================================================================================

SELECT
    'cierres' as tabla,
    COUNT(*) as total_registros
FROM modelo_ventas_rauco.cierres

UNION ALL

SELECT 'cierres_detalle', COUNT(*)
FROM modelo_ventas_rauco.cierres_detalle

UNION ALL

SELECT 'cierres_precio_producto', COUNT(*)
FROM modelo_ventas_rauco.cierres_precio_producto

UNION ALL

SELECT 'cierres_medio_pago', COUNT(*)
FROM modelo_ventas_rauco.cierres_medio_pago

UNION ALL

SELECT 'cierres_depositos', COUNT(*)
FROM modelo_ventas_rauco.cierres_depositos

UNION ALL

SELECT 'cierres_guias', COUNT(*)
FROM modelo_ventas_rauco.cierres_guias

UNION ALL

SELECT 'cierres_guias_detalle', COUNT(*)
FROM modelo_ventas_rauco.cierres_guias_detalle

ORDER BY tabla;
