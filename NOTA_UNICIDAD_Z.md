# 🔑 NOTA CRÍTICA: Unicidad de Z (znumber)

**Estatus:** ⚠️ IMPORTANTE ENTENDER

---

## ❌ **INCORRECTO**

```
Z es único por sí solo

Z=1056 → identifica exactamente UN cierre
```

---

## ✅ **CORRECTO**

```
La COMBINACIÓN (localid + pos + Z) es única

(localid=259, pos=1, z=1056) → identifica exactamente UN cierre
(localid=260, pos=1, z=1056) → cierre DIFERENTE (otro local)
(localid=259, pos=2, z=1056) → cierre DIFERENTE (otra caja)
```

---

## 📊 **Ejemplo Visual**

```
Database: geocom.totals

Registro 1:
  localid=259, pos=1, znumber=1056, closed=20260102
  ↓ Este es UN cierre específico

Registro 2:
  localid=259, pos=2, znumber=1056, closed=20260103
  ↓ Diferente cierre (misma tienda, otra caja)

Registro 3:
  localid=260, pos=1, znumber=1056, closed=20260102
  ↓ Diferente cierre (otra tienda)

Conclusión: Z=1056 aparece 3 veces en la BD
            pero son 3 cierres completamente diferentes
```

---

## 🔍 **Dónde se Implementa Correctamente**

### **1. En `src/main.py` - Verificación de duplicados**

✅ **CORRECTO:**
```python
if Z_LIST:
    query_distinct_header = f"""
        SELECT DISTINCT id
        FROM cierres
        WHERE localid = {LOCALID}      ← ✅ Filtra por tienda
        AND pos = {POS}                ← ✅ Filtra por caja
        AND znumber IN ({z_str})       ← Filtra por Z
    """
```

### **2. En `src/main.py` - Query principal de cierres**

✅ **CORRECTO:**
```python
query_cierres = f"""
    SELECT ... FROM totals
    WHERE localid = {LOCALID}          ← ✅ Tienda específica
    AND pos = {POS}                    ← ✅ Caja específica
    AND znumber IN ({z_str})           ← ✅ Z específico
"""
```

### **3. En `src/qa_missing_cierres.py` - Tests**

✅ **CORRECTO:**
```python
def test_cierre_exists_in_geocom(self, localid, pos, znumber):
    query = f"""
        SELECT COUNT(*) FROM totals
        WHERE localid = {localid}      ← ✅ Tienda
        AND pos = {pos}                ← ✅ Caja
        AND znumber = {znumber}        ← ✅ Z
    """

def test_data_consistency(self, id_cierre, localid, pos, znumber):
    query_detail = f"""
        SELECT COUNT(*) FROM cierres_detalle
        WHERE localid = {localid}      ← ✅ Tienda
        AND pos = {pos}                ← ✅ Caja
        AND z = {znumber}              ← ✅ Z
    """
```

---

## 🎯 **Línea de Comando - Qué Significa**

```bash
python run.py --modulos VENTAS \
  --localid 259 \     ← Tienda 259
  --pos 1 \          ← Caja 1 de esa tienda
  --z 1056           ← Cierre Z=1056 de esa tienda/caja específica
```

**NO significa:** "Procesa ALL Z=1056 en la BD"
**SIGNIFICA:** "Procesa Z=1056 SOLO en la combinación local 259, caja 1"

---

## ⚠️ **Errores Comunes (QUE NO OCURREN)**

### ❌ Error 1: Olvidar localid/pos

```python
# INCORRECTO (no hacemos esto):
WHERE znumber = 1056  ← Traería 3+ cierres diferentes

# CORRECTO (lo que hacemos):
WHERE localid = 259 AND pos = 1 AND znumber = 1056  ← 1 cierre exacto
```

### ❌ Error 2: Asumir Z es único globalmente

```python
# INCORRECTO (no lo asumimos):
# "Si Z=1056 existe en cierres → omitir"
# → Podría haber Z=1056 de otra tienda/caja

# CORRECTO (lo que hacemos):
# "Si (local=259, pos=1, z=1056) existe → omitir"
# → Exactamente ese cierre
```

---

## 📋 **Matriz de Validación**

| Escenario | Consulta | Resultado |
|-----------|----------|-----------|
| Buscar Z=1056 en local 259, caja 1 | `localid=259, pos=1, z=1056` | ✅ 1 registro |
| Buscar Z=1056 en local 260, caja 1 | `localid=260, pos=1, z=1056` | ✅ 1 registro diferente |
| Buscar TODOS los Z=1056 | `z=1056` sin localid/pos | ❌ NO LO HACEMOS (traería múltiples) |

---

## 🛡️ **Garantía de Implementación**

```
✅ GARANTIZADO:
   - Siempre filtramos por (localid, pos, Z)
   - Nunca procesamos solo por Z
   - Cada cierre es único en su combinación
   - No hay riesgo de procesar cierre equivocado
   - No hay riesgo de contaminar otra tienda/caja
```

---

## 📌 **Resumen Técnico**

| Aspecto | Estado |
|---------|--------|
| Z es único globalmente | ❌ NO |
| (localid, pos, Z) es único | ✅ SÍ |
| Código implementa correctamente | ✅ SÍ |
| Documentación clara | ⚠️ AHORA SÍ (este documento) |
| Riesgo de error | 🟢 BAJO |

---

**Versión:** 1.0
**Crítico:** SÍ (para entendimiento)
**Impacto:** Cero (si lo entiendes; máximo si lo olvidas)
