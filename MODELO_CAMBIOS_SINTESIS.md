# 📋 Síntesis: Modelo de Cierres con Búsqueda Directa por Z

**Fecha:** Marzo 2026
**Objetivo:** Permitir cargar cierres de caja específicos sin procesar otros del mismo período

---

## 🎯 Cambios Principales en el Modelo

### **1. De búsqueda por fechas → búsqueda por Z (znumber)**

#### Antes:
```bash
python run.py --modulos VENTAS MEDIOS_PAGO \
  --localid 259 --pos 1 \
  --fecha_ini 20260102 --fecha_fin 20260102
# Problema: procesa TODOS los cierres de ese día en esa caja
```

#### Ahora:
```bash
python run.py --modulos VENTAS MEDIOS_PAGO \
  --localid 259 --pos 1 \
  --z 1056
# ✅ Procesa SOLO el cierre Z=1056 de esa caja/tienda
```

### **2. Parámetros de run.py (actualizados)**

| Parámetro | Antes | Ahora |
|-----------|-------|-------|
| `--modulos` | Obligatorio | Obligatorio |
| `--localid` | Obligatorio | Obligatorio |
| `--pos` | Obligatorio | Obligatorio |
| `--z` | ❌ No existía | ✅ Nuevo (nargs='+') |
| `--fecha_ini` | Obligatorio | Opcional (si no usa --z) |
| `--fecha_fin` | Obligatorio | Opcional (si no usa --z) |

**Validación:** Se debe pasar `--z` O ambas fechas (mutuamente excluyentes)

---

## 🔄 Flujo Completo: QA → PROD

### **PASO 1: Identificar cierres faltantes**

Script: `process_missing_cierres.py`

```bash
python process_missing_cierres.py
```

**Qué hace:**
1. Compara `geocom.totals` vs `DW.cierres`
2. Identifica cierres que faltan cargar
3. Extrae: `localid`, `pos`, `znumber`, `closed_date`

**Salida:** Listado de cierres faltantes
```
CIERRES FALTANTES EN DW:
Local 259:
  POS 1: 3 cierre(s) faltante(s)
    - Closed: 20260102 | ID: 2601022048302591 | Z: 1056
    - Closed: 20260103 | ID: 2601032048302591 | Z: 1057
    - Closed: 20260104 | ID: 2601042048302591 | Z: 1058
```

---

### **PASO 2: QA - Validar datos antes de cargar**

Script: `src/qa_missing_cierres.py`

**Tests por cierre:**
```
🔍 Ejecutando QA para cierre 259-1-Z1056 (20260102)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Cierre existe en geocom
  ✓ Datos de ventas existen (173 tickets)
  ✓ Datos de medios pago existen (167 pagos)
  ✓ Cierre NO existe en DW (validación de faltante)
  ✓ Detalle NO existe en DW
```

**Resumen final (compacto):**
```
📊 TOTALES:
   Total de tests ejecutados: 35
   ✓ PASS:     35    (100%)
   ⚠️  WARNING:  0     (  0%)
   ✗ FAIL:     0     (  0%)
   ✗ ERROR:    0     (  0%)

📋 RESUMEN POR TIPO DE TEST:
   Cierre existe en geocom           ✓7 ⚠0 ✗0 E0
   Datos de ventas existen           ✓7 ⚠0 ✗0 E0
   Datos de medios pago existen      ✓7 ⚠0 ✗0 E0
   Cierre NO existe en DW            ✓7 ⚠0 ✗0 E0
   Detalle del cierre NO existe      ✓7 ⚠0 ✗0 E0
```

**Búsqueda por Z garantiza:** Valida exactamente ese cierre (Z=1056), no otros del mismo día

---

### **PASO 3: Generar script de ejecución**

Salida: `missing_cierres_commands.sh`

```bash
#!/bin/bash
# Script generado automáticamente para procesar cierres faltantes
# Generado: 2026-03-16 14:23:45
# Modo: Ejecución directa por Z (znumber) - sin fechas
# NOTA: Ejecutar solo en PROD después de QA

# Local 259 | POS 1 | Z 1056 | Closed 20260102
python run.py --modulos VENTAS MEDIOS_PAGO REDONDEOS DEPOSITOS GUIAS --localid 259 --pos 1 --z 1056

# Local 259 | POS 1 | Z 1057 | Closed 20260103
python run.py --modulos VENTAS MEDIOS_PAGO REDONDEOS DEPOSITOS GUIAS --localid 259 --pos 1 --z 1057

# Local 259 | POS 1 | Z 1058 | Closed 20260104
python run.py --modulos VENTAS MEDIOS_PAGO REDONDEOS DEPOSITOS GUIAS --localid 259 --pos 1 --z 1058
```

---

### **PASO 4: Ejecutar en PROD**

En Windows (con Git Bash):
```bash
bash missing_cierres_commands.sh
```

O ejecutar manualmente:
```bash
python run.py --modulos VENTAS MEDIOS_PAGO REDONDEOS DEPOSITOS GUIAS --localid 259 --pos 1 --z 1056
```

---

## 🔧 Cómo Funciona Ahora el Código

### **run.py - Entrada de parámetros**

```python
# Validación: se debe pasar --z O (fecha_ini Y fecha_fin)
if not args.z and not (args.fecha_ini and args.fecha_fin):
    parser.error("Se debe especificar --z o ambos --fecha_ini y --fecha_fin")

# En modo Z, localid y pos son obligatorios
if args.z:
    if args.localid == "None" or args.pos == "None":
        parser.error("En modo --z, --localid y --pos son obligatorios")
```

### **src/main.py - procesar_cierres()**

```python
Z_LIST = config.get('z', None)

# MODO Z: Busca cierres específicos por znumber
if Z_LIST:
    z_str = ','.join(map(str, Z_LIST))
    print(f">> Modo Z: procesando znumbers={Z_LIST}")

    # Query con filtro por Z
    query = f"""
        SELECT ... FROM totals curr
        WHERE curr.localid = {LOCALID}
            AND curr.pos = {POS}
            AND curr.znumber IN ({z_str})  ← ✅ BÚSQUEDA POR Z
            AND curr.localid BETWEEN 100 AND 999
    """

# MODO FECHA: Comportamiento original (sin cambios)
else:
    print(f">> Procesando cierres, fechas={PAR_INI}-{PAR_FIN}")
    query = f"""
        ... WHERE ...
        AND CAST(CONVERT(VARCHAR, curr.closed, 112) AS INT) BETWEEN {PAR_INI} AND {PAR_FIN}
    """
```

### **Verificación de duplicados (según modo)**

```python
# MODO Z: busca por localid, pos, znumber
if Z_LIST:
    z_str = ','.join(map(str, Z_LIST))
    query_distinct = f"""
        SELECT DISTINCT id FROM cierres
        WHERE localid = {LOCALID}
            AND pos = {POS}
            AND znumber IN ({z_str})  ← ✅ ÚNICAMENTE ESTE Z
    """
else:
    # Modo fecha: búsqueda por fecha
    query_distinct = f"""
        SELECT DISTINCT id FROM cierres
        WHERE CAST(CONVERT(VARCHAR, closed, 112) AS INT) BETWEEN {PAR_INI} AND {PAR_FIN}
    """

# Si existe → se omite (NO se procesa nuevamente)
df_dup = df_totals[df_totals['id'].isin(df_distinct['id'].tolist())]
print(f">> Cierres ya procesados: {len(df_dup)}. Se eliminan de la lista...")
```

### **src/qa_missing_cierres.py - Validación por Z**

```python
def test_cierre_exists_in_geocom(self, localid, pos, znumber):
    """Busca por znumber para garantizar granularidad"""
    query = f"""
        SELECT COUNT(*) as count_totals
        FROM totals
        WHERE localid = {localid}
            AND pos = {pos}
            AND znumber = {znumber}  ← ✅ EXACTAMENTE ESTE Z
    """

def test_cierre_detail_NOT_in_dw(self, localid, pos, znumber):
    """Valida que los detalles del cierre NO existan en DW"""
    query = f"""
        SELECT COUNT(*) as count_details
        FROM cierres_detalle
        WHERE localid = {localid}
            AND pos = {pos}
            AND z = {znumber}  ← ✅ BÚSQUEDA GRANULAR
    """
```

---

## ⚠️ Advertencias y Protecciones

### **1. NO BORRA información existente**

```
Garantía 1: Verificación de duplicados
├─ ANTES de insertar: verifica si el cierre ya existe en DW
├─ Si existe: SE OMITE (no se procesa nuevamente)
└─ Si no existe: SE CARGA

Garantía 2: Inserción con IF_EXISTS='append'
├─ Usa pandas to_sql(..., if_exists='append', ...)
├─ NUNCA reemplaza tablas existentes
└─ Solo AGREGA nuevos registros
```

### **2. Protección contra recargas accidentales**

```bash
# Escenario: Intentas ejecutar el mismo Z dos veces
$ python run.py --modulos VENTAS --localid 259 --pos 1 --z 1056
# Primera ejecución: ✓ Se carga
# Segunda ejecución: ⚠️ "Cierres ya procesados: 1. Se eliminan de la lista..."
```

### **3. Granularidad máxima**

```
Antes:  --fecha_ini 20260102 --fecha_fin 20260102
        → Procesa 5 cierres del día (Z=1000, 1001, 1002, 1003, 1004)
        → Riesgo: alguno ya podría estar en DW

Ahora:  --z 1056
        → Procesa EXACTAMENTE un cierre
        → Sin ambigüedad
        → Sin accidentes
```

### **4. Módulos selectivos**

```bash
# Carga todo
python run.py --modulos VENTAS MEDIOS_PAGO REDONDEOS DEPOSITOS GUIAS \
  --localid 259 --pos 1 --z 1056

# Solo ventas
python run.py --modulos VENTAS \
  --localid 259 --pos 1 --z 1056

# Puedes ejecutar parcialmente y repetir sin riesgo
```

---

## 📊 Ejemplo Completo: Z=1056, Local 259, POS 1

### **Input (QA encontró esto)**
```
Local 259 | POS 1 | Z 1056 | Closed 20260102
  - 173 tickets de ventas
  - 167 registros de medios pago
  - NO existe en DW
```

### **QA Validation**
```
✓ PASS | Cierre existe en geocom
        Encontrados 3 registros

✓ PASS | Datos de ventas existen en geocom
        Encontrados 173 tickets

✓ PASS | Datos de medios pago existen en geocom
        Encontrados 167 pagos

✓ PASS | Cierre NO existe en DW (validación de faltante)
        Encontrados 0 registros en DW (esperaba 0)

✓ PASS | Detalle del cierre NO existe en DW
        Encontrados 0 registros en detalle (esperaba 0)
```

### **Comando generado**
```bash
python run.py --modulos VENTAS MEDIOS_PAGO REDONDEOS DEPOSITOS GUIAS \
  --localid 259 --pos 1 --z 1056
```

### **Ejecución en PROD**
```
>> Modo Z: procesando znumbers=[1056]
>> LOCALID=259
>> POS=1

>> Se encontraron un total de 1 cierres pre-filtro de duplicados.
>> Cierres ya procesados: 0. Se eliminan de la lista de cierres a procesar.
>> Se encontraron un total de 1 cierres para los filtros aplicados.

>> Ejecución en curso - Cierre: 1
>> Ejecutando Ventas
   [inserta 173 registros en cierres_detalle]
   [inserta precio productos]
   [inserta en cierres_cabecera]

>> Ejecutando Medios de Pago
   [inserta 167 registros en cierres_medio_pago]

>> Ejecución finalizada.
```

### **Resultado en DW**
```
✓ 1 cierre cargado (id: 2601022048302591)
✓ 173 detalles de ventas cargados
✓ 167 medios de pago cargados
✓ 1 cabecera cargada
```

---

## 🛡️ Resumen de Protecciones

| Protección | Mecanismo | Garantía |
|------------|-----------|----------|
| **No duplicados** | `query_distinct` verifica antes de insertar | Si existe → se omite |
| **Granularidad** | Búsqueda por `znumber` exacto | Un Z = un cierre |
| **No sobrescribe** | `if_exists='append'` en pandas | Solo agrega, nunca reemplaza |
| **Trazabilidad** | Script generado con fecha/hora | Auditoría completa |
| **QA previo** | Validación antes de PROD | Datos verificados |
| **Selectividad** | Módulos configurables | Control total |

---

## ✅ Checklist Antes de Ejecutar en PROD

- [ ] Ejecutar `process_missing_cierres.py` y revisar lista de faltantes
- [ ] Revisar reporte QA (`qa_missing_cierres.csv`) - todos PASS
- [ ] Revisar `missing_cierres_commands.sh` - comandos correctos
- [ ] Ejecutar en ambiente DEV/QA primero (si es posible)
- [ ] Hacer backup de DW (por precaución)
- [ ] Ejecutar script en PROD: `bash missing_cierres_commands.sh`
- [ ] Verificar registros insertados en DW
- [ ] Comparar conteos: geocom vs DW (deben coincidir)

---

**Versión:** 1.0
**Estado:** ✅ Listo para PROD
**Riesgo:** 🟢 BAJO (protecciones activas)
