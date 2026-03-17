# Manejo de Reinicio de Contador Z

## El Problema

El contador Z (znumber) en cada caja (localid + pos) **no es globalmente único**. El contador se reinicia periódicamente (cada 100, 1000, o N transacciones según configuración), lo que significa que puede haber múltiples cierres con la **misma combinación (localid + pos + z)**.

### Ejemplo Real

En tu caso, Local 333 POS 1:

```
2025-11-28 11:48:35 -> closed 2025-11-28 14:05:19 | Z=1
2026-03-11 10:17:45 -> closed 2026-03-11 17:09:29 | Z=1  <-- Mismo Z, pero ~3.5 meses después
```

Estos son DOS cierres completamente diferentes, pero con el **mismo znumber**.

## La Solución Implementada

### 1. Deduplicación por Fecha

La clave única real es: **(localid + pos + z + fecha_closed)**

Cuando buscas por Z y hay duplicados, se filtra por la fecha para desambiguar:

```bash
# Sin desambiguar (ambiguo si Z se repitió):
python run.py --localid 333 --pos 1 --z 1

# Con desambiguar (específico para el cierre de 2026-03-11):
python run.py --localid 333 --pos 1 --z 1 --fecha_ini 20260311 --fecha_fin 20260311
```

### 2. Detección Automática en process_missing_cierres.py

Cuando `process_missing_cierres.py` genera comandos:

- **Si detecta un Z duplicado**: Automáticamente agrega `--fecha_ini` y `--fecha_fin` para desambiguar
- **Ejemplo de comando generado con reinicio**:
  ```
  python run.py --localid 333 --pos 1 --z 1 --fecha_ini 20260311 --fecha_fin 20260311
  ```

### 3. Comportamiento de run.py

- `--z` es **opcional pero recomendado** cuando conoces el Z number
- `--fecha_ini` y `--fecha_fin` son **opcionales**
- Si especificas ambos: Se filtra por `(localid + pos + z + fecha_range)`
- Si solo especificas `--z`: Se usa `fecha_actual` por defecto

### 4. Formato de Fecha

- Siempre usar: **YYYYMMDD** (ej: 20260311)
- Python convierte automáticamente el timestamp `closed` a este formato

## Implicaciones en el ETL

### Verificación de Duplicados

El sistema ahora verifica duplicados considerando:

```sql
-- En modo Z, verifica:
WHERE localid = X
  AND pos = Y
  AND znumber IN (z_values)
  AND CAST(CONVERT(VARCHAR, closed, 112) AS INT) BETWEEN fecha_ini AND fecha_fin
```

Esto garantiza que:
- ✓ No reinsertes un cierre que ya existe
- ✓ Permites múltiples cierres con el mismo Z (en fechas diferentes)
- ✓ El ID del cierre incluye timestamp completo (es único automáticamente)

### ID del Cierre

El ID se genera así:

```sql
YYYYMMDDHHMMSS + localid + pos
```

Ejemplo:
- Z=1 del 2025-11-28 14:05:19 -> ID: `20251128140519333 1`
- Z=1 del 2026-03-11 17:09:29 -> ID: `20260311170929333 1`

Son IDs completamente diferentes, aunque tengan el mismo Z.

## Casos de Uso

### Caso 1: Procesar un Z único (sin reinicio)

```bash
python run.py --modulos VENTAS MEDIOS_PAGO --localid 259 --pos 1 --z 1056
```

### Caso 2: Procesar un Z que se repitió (reinicio detectado)

```bash
# Opción A: Dejar que process_missing_cierres.py lo detecte y agregue las fechas automáticamente
python process_missing_cierres.py

# Opción B: Hacerlo manualmente
python run.py --modulos VENTAS MEDIOS_PAGO --localid 333 --pos 1 --z 1 --fecha_ini 20260311 --fecha_fin 20260311
```

### Caso 3: Procesar por rango de fechas (sin Z)

```bash
python run.py --modulos VENTAS MEDIOS_PAGO --fecha_ini 20260310 --fecha_fin 20260312
```

## Validación y Seguridad

- ✓ El sistema previene duplicados en BD
- ✓ Si Z se repite, el ID basado en timestamp evita conflictos
- ✓ QA detecta casos anómalos (cierres sin detalle, detalle sin cierre)
- ✓ Dry-run permite validar antes de escribir en BD

## Referencia Rápida

| Parámetro | Obligatorio | Descripción |
|-----------|-------------|-------------|
| `--modulos` | Sí | Módulos a procesar |
| `--z` | No* | Z number (si no, usar `--fecha_ini/fin`) |
| `--fecha_ini` | No* | Fecha inicial para desambiguar Z o rango de fechas |
| `--fecha_fin` | No* | Fecha final para desambiguar Z o rango de fechas |
| `--localid` | Sí (con `--z`) | Número de local |
| `--pos` | Sí (con `--z`) | Número de caja |
| `--dry-run` | No | Ejecutar sin escribir en BD |

*Debe especificarse `--z` O ambos (`--fecha_ini` Y `--fecha_fin`)
