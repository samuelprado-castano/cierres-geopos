-- ============================================================================
-- QUERIES DE VALIDACIÓN DE CIERRES FALTANTES
-- Cruce entre geocom.totals y DW.cierres
-- NOTA: Como son servidores distintos, usar las queries por separado
-- ============================================================================

-- ============================================================================
-- EJECUTAR EN SERVIDOR GEOCOM
-- ============================================================================

-- 1. Total de cierres en geocom para enero 2026
SELECT
    COUNT(*) as total_cierres_geocom
FROM totals
WHERE CAST(CONVERT(VARCHAR, closed, 112) AS INT) BETWEEN 20260101 AND 20260131
GO

-- 2. Desglose por local y POS en geocom
SELECT
    localid,
    pos,
    COUNT(*) as cantidad_cierres,
    MIN(closed) as primer_cierre,
    MAX(closed) as ultimo_cierre
FROM totals
WHERE CAST(CONVERT(VARCHAR, closed, 112) AS INT) BETWEEN 20260101 AND 20260131
GROUP BY localid, pos
ORDER BY localid, pos
GO

-- 3. Listado completo de cierres en geocom (enero 2026)
SELECT
    id,
    localid,
    pos,
    opened,
    closed,
    ticketnumber_opened,
    ticketnumber_closed,
    znumber
FROM totals
WHERE CAST(CONVERT(VARCHAR, closed, 112) AS INT) BETWEEN 20260101 AND 20260131
ORDER BY localid, pos, closed
GO

-- ============================================================================
-- EJECUTAR EN SERVIDOR DW
-- ============================================================================

-- 4. Total de cierres en DW para enero 2026
SELECT
    COUNT(*) as total_cierres_dw
FROM modelo_ventas_rauco.cierres
WHERE CAST(CONVERT(VARCHAR, closed, 112) AS INT) BETWEEN 20260101 AND 20260131
GO

-- 5. Desglose por local y POS en DW
SELECT
    localid,
    pos,
    COUNT(*) as cantidad_cierres,
    MIN(closed) as primer_cierre,
    MAX(closed) as ultimo_cierre
FROM modelo_ventas_rauco.cierres
WHERE CAST(CONVERT(VARCHAR, closed, 112) AS INT) BETWEEN 20260101 AND 20260131
GROUP BY localid, pos
ORDER BY localid, pos
GO

-- 6. Listado completo de cierres en DW (enero 2026)
SELECT
    id,
    localid,
    pos,
    opened,
    closed
FROM modelo_ventas_rauco.cierres
WHERE CAST(CONVERT(VARCHAR, closed, 112) AS INT) BETWEEN 20260101 AND 20260131
ORDER BY localid, pos, closed
GO

-- ============================================================================
-- PARA HACER EL CRUCE Y ENCONTRAR FALTANTES:
-- Usar el script Python: python process_missing_cierres.py
-- ============================================================================
