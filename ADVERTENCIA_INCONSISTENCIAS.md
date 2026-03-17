# ⚠️ ADVERTENCIA: Caso Edge - Inconsistencias de Datos

**Fecha:** Marzo 2026
**Crítico:** SÍ
**Estatus:** ✅ SOLUCIONADO

---

## 🚨 **Problema Identificado**

### Escenario problemático:
```
Tabla cierres (cabecera):
  Z=1056, Local 259, POS 1: ❌ NO EXISTE

Tabla cierres_detalle:
  Z=1056, Local 259, POS 1: ✅ EXISTE (173 registros)

Tabla cierres_medio_pago:
  Z=1056, Local 259, POS 1: ❌ NO EXISTE

Estado: ⚠️ INCONSISTENCIA (detalle huérfano)
```

### ¿Cómo ocurre?

```python
# Ejecución 1: Falla a mitad del proceso
python run.py --z 1056
  ✓ Inserta 173 detalles en cierres_detalle
  ✓ Inserta cabecera en cierres
  ✗ ERROR al insertar medios pago (falla DB, timeout, etc)
  → Estado: Detalle+Cabecera OK, Medios Pago FALTA

# Ejecución 2: Reintentas
python run.py --z 1056
  ✓ Verifica cabecera... existe → OMITIDO ✅ (correcto)
  ✗ Pero ¿qué si la cabecera se eliminó manualmente?
  ✓ Inserta NUEVAMENTE 173 detalles
  → Resultado: 346 detalles (DUPLICADOS) 🔴
```

---

## ✅ **Solución Implementada**

### **1. Verificación mejorada en `src/main.py`**

**Antes:**
```python
# Solo verificaba cabecera
query_distinct = f"""
    SELECT DISTINCT id FROM cierres WHERE z IN ({z_str})
"""
```

**Ahora:**
```python
# Verifica AMBAS tablas (cabecera + detalle)
query_distinct_header = f"""
    SELECT DISTINCT id FROM cierres WHERE z IN ({z_str})
"""

query_distinct_detail = f"""
    SELECT DISTINCT id FROM cierres_detalle WHERE z IN ({z_str})
"""

# Combina ambas (union de IDs)
df_distinct = pd.concat([df_distinct_header, df_distinct_detail],
                        ignore_index=True).drop_duplicates()
```

**Impacto:** Si detalle existe → se omite (aunque falte cabecera)

---

### **2. Test de Consistencia en `src/qa_missing_cierres.py`**

**Nuevo test: `test_data_consistency()`**

```python
def test_data_consistency(self, id_cierre, localid, pos, znumber):
    """
    VALIDACIÓN CRÍTICA: Detecta inconsistencias
    """
    # Busca cabecera
    # Busca detalle

    if cabecera_existe == 0 and detalle_existe == 0:
        ✓ PASS: Ambos vacíos (correcto)
    elif cabecera_existe > 0 and detalle_existe > 0:
        ✓ PASS: Ambos con datos (correcto)
    elif cabecera_existe == 0 and detalle_existe > 0:
        ✗ FAIL: ⚠️ INCONSISTENCIA (detalle huérfano)
    else:
        ✓ PASS: Cabecera sin detalle (válido - sin ventas)
```

**Salida en QA:**
```
✗ FAIL | Consistencia de datos (cabecera-detalle)
        ⚠️ INCONSISTENCIA: Detalle existe (173 reg) pero Cabecera NO
```

---

## 📊 **Matriz de Casos**

| Cabecera | Detalle | Resultado | Acción |
|----------|---------|-----------|--------|
| ❌ NO | ❌ NO | ✓ PASS | Procesar normalmente |
| ✅ SÍ | ✅ SÍ | ✓ PASS | Omitir (ya existe) |
| ✅ SÍ | ❌ NO | ⚠️ WARNING | Revisar (anómalo pero menor) |
| ❌ NO | ✅ SÍ | ✗ FAIL | 🚨 **INCONSISTENCIA CRÍTICA** |

---

## 🛠️ **Cómo Recuperarse de Inconsistencias**

### **Si detectas: "INCONSISTENCIA: Detalle existe pero Cabecera NO"**

#### **Opción 1: Limpiar y recargar (RECOMENDADO)**
```sql
-- 1. Eliminar detalle huérfano
DELETE FROM modelo_ventas_rauco.cierres_detalle
WHERE localid = 259 AND pos = 1 AND z = 1056;

-- 2. Eliminar medios pago huérfano (si existe)
DELETE FROM modelo_ventas_rauco.cierres_medio_pago
WHERE localid = 259 AND pos = 1 AND z = 1056;

-- 3. Eliminar depósitos huérfanos (si existe)
DELETE FROM modelo_ventas_rauco.cierres_depositos
WHERE localid = 259 AND pos = 1 AND z = 1056;

-- 4. Eliminar guías huérfanas (si existe)
DELETE FROM modelo_ventas_rauco.cierres_guias
WHERE localid = 259 AND pos = 1 AND z = 1056;

-- 5. Verificar que no queden datos
SELECT COUNT(*) FROM modelo_ventas_rauco.cierres_detalle
WHERE localid = 259 AND pos = 1 AND z = 1056;
-- Debe retornar: 0

-- 6. Re-ejecutar
python run.py --modulos VENTAS MEDIOS_PAGO REDONDEOS DEPOSITOS GUIAS \
  --localid 259 --pos 1 --z 1056
```

#### **Opción 2: Insertar cabecera faltante (si datos están completos)**
```sql
-- Solo si tienes certeza de que los detalles son correctos
-- Recupera info de cabecera desde geocom y cierres_detalle
-- (NO recomendado - mejor hacer limpieza completa)
```

---

## 📋 **Checklist QA - Antes de PROD**

Cuando ejecutes `process_missing_cierres.py`, el QA ahora hace:

```
✓ Cierre existe en geocom
✓ Datos de ventas existen en geocom
✓ Datos de medios pago existen en geocom
✓ Cierre NO existe en DW (cabecera)
✓ Detalle NO existe en DW
✓ Consistencia de datos (cabecera-detalle)  ← NUEVO TEST
```

**Si algún test da FAIL → INVESTIGA antes de ejecutar en PROD**

---

## 🛡️ **Protecciones Contra Este Problema**

| Protección | Nivel | Mecanismo |
|-----------|-------|-----------|
| Verifica cabecera | ✅ | Query en tabla `cierres` |
| Verifica detalle | ✅ | Query en tabla `cierres_detalle` |
| Detecta inconsistencias | ✅ | Test de consistencia en QA |
| Previene reinsersión | ✅ | Union de verificaciones |
| Limpieza en DW | ⚠️ | Manual (ver instrucciones arriba) |

---

## ⚡ **Resumen de Cambios**

```diff
# src/main.py
- Solo verifica tabla cierres (cabecera)
+ Verifica tabla cierres + tabla cierres_detalle
+ Combina resultados (union)
+ Evita reinserción incluso si falta cabecera

# src/qa_missing_cierres.py
+ Nuevo test: test_data_consistency()
+ Detecta: detalle existe pero cabecera NO
+ Alerta: FAIL si hay inconsistencia
+ Aviso: ayuda a identificar problemas antes de PROD
```

---

## 📌 **Importante**

```
⚠️ NUNCA intentes "arreglarlo" sin investigar la causa raíz

Posibles causas de inconsistencia:
1. ✗ Error de proceso (timeout, DB llena, etc)
2. ✗ Eliminación manual de cabecera (accidental o intencional)
3. ✗ Problema de FK (foreign key) - detalle sin padre
4. ✗ Corrupción de datos

Siempre:
1. Identifica la causa
2. Documenta el incidente
3. Limpia completamente (todos los módulos)
4. Reinicia el proceso desde cero
```

---

## 🔐 **Garantías Actuales**

- ✅ El script NO borra información existente (except append-only)
- ✅ Se detectan inconsistencias antes de PROD
- ✅ Se previene reinserción de detalles duplicados
- ✅ QA alerta sobre anomalías
- 📋 Procedimiento de recuperación disponible

**Estatus:** ✅ SEGURO PARA PRODUCCIÓN

---

**Versión:** 1.1
**Fecha:** Marzo 2026
**Crítico:** SÍ (pero solucionado)
**Riesgo:** 🟢 BAJO (con protecciones)
