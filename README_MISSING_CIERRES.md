# Procesamiento de Cierres Faltantes

## Descripción General

Este conjunto de scripts identifica y procesa cierres que existen en `geocom.totals` pero no han sido cargados en `DW.cierres`. El flujo es:

1. **Validación**: Cruzar datos entre `geocom.totals` y `DW.cierres`
2. **QA**: Validar que los datos de los módulos existan en geocom y NO en DW
3. **Generación de comandos**: Preparar los comandos para ejecutar `run.py` (sin ejecutar aún)
4. **PROD**: Ejecutar los comandos en producción

## Archivos Creados

### 1. `process_missing_cierres.py` ⭐ PRINCIPAL
Script que orquesta todo el flujo. Ejecutar este para obtener resumen completo.

**Uso:**
```bash
python process_missing_cierres.py
```

**Salida:**
- `qa_missing_cierres.csv` - Reporte detallado de QA
- `missing_cierres_commands.sh` - Script con todos los comandos para ejecutar en PROD

### 2. `src/missing_cierres.py`
Módulo con la clase `MissingCierresProcessor` que:
- Obtiene cierres de `geocom.totals`
- Obtiene cierres de `DW.cierres`
- Compara y encuentra los faltantes por `localid`, `pos`, `closed`

**Métodos principales:**
```python
processor = MissingCierresProcessor()

# Buscar cierres faltantes
df_missing = processor.find_missing_cierres("20260101", "20260131")

# Validar un cierre específico
cierre = processor.validate_closure_data(localid=1, pos=1, closed=20260105)
```

### 3. `src/qa_missing_cierres.py`
Módulo con la clase `QAMissingCierres` que valida:

- ✓ Cierre existe en `geocom.totals`
- ✓ Datos de ventas existen en geocom
- ✓ Datos de medios de pago existen en geocom
- ✓ Cierre NO existe en `DW.cierres` (validación de faltante)
- ✓ Detalle del cierre NO existe en `DW.cierres_detalle`

**Uso:**
```python
qa = QAMissingCierres()
qa.run_qa_for_multiple_cierres(df_missing)
qa.print_qa_report()
qa.export_qa_report('reporte.csv')
```

### 4. `validation_query.sql`
Queries SQL para validar datos manualmente:

**En GEOCOM:**
```sql
-- Listar todos los cierres de enero 2026
SELECT ... FROM totals WHERE closed BETWEEN 20260101 AND 20260131

-- Contar por local y POS
SELECT localid, pos, COUNT(*) ... GROUP BY localid, pos
```

**En DW:**
```sql
-- Listar cierres cargados en DW
SELECT ... FROM modelo_ventas_rauco.cierres WHERE closed BETWEEN 20260101 AND 20260131
```

## Flujo de Ejecución

### PASO 1: Identificar Cierres Faltantes

```bash
python process_missing_cierres.py
```

**Salida esperada:**
```
RESUMEN DEL PERÍODO 20260101-20260131:
   - Cierres en geocom.totals: 300
   - Cierres en DW.cierres: 127
   - Cierres faltantes: 173  ✓ Coincide con expectativa
```

### PASO 2: Revisar Reporte QA

El script genera `qa_missing_cierres.csv` con todos los tests:

| test | localid | pos | closed | status | details |
|------|---------|-----|--------|--------|---------|
| Cierre existe en geocom | 1 | 1 | 20260105 | ✓ PASS | Encontrados 1 registros |
| Datos de ventas... | 1 | 1 | 20260105 | ✓ PASS | Encontrados 156 tickets |
| Datos de medios pago... | 1 | 1 | 20260105 | ✓ PASS | Encontrados 145 pagos |
| Cierre NO existe en DW | 1 | 1 | 20260105 | ✓ PASS | Encontrados 0 registros en DW |
| Detalle NO existe en DW | 1 | 1 | 20260105 | ✓ PASS | Encontrados 0 registros |

**Si hay errores (✗ FAIL):**
- Revisar el detalle en la columna `details`
- Investigar en bases de datos
- NO proceder a PROD hasta que todos los tests pasen

### PASO 3: Ejecutar en PROD (Cuando sea aprobado)

El script genera `missing_cierres_commands.sh` con todos los comandos:

```bash
# Local 1 | POS 1 | Closed 20260105
python run.py --modulos VENTAS MEDIOS_PAGO ANULACIONES --localid 1 --pos 1 --fecha_ini 20260105 --fecha_fin 20260105

# Local 1 | POS 1 | Closed 20260106
python run.py --modulos VENTAS MEDIOS_PAGO ANULACIONES --localid 1 --pos 1 --fecha_ini 20260106 --fecha_fin 20260106
...
```

**Para ejecutar:**
```bash
# Revisar primero los comandos
cat missing_cierres_commands.sh

# Ejecutar (cuando sea aprobado)
bash missing_cierres_commands.sh
```

**O ejecutar uno a uno para monitorear:**
```bash
python run.py --modulos VENTAS MEDIOS_PAGO ANULACIONES --localid 1 --pos 1 --fecha_ini 20260105 --fecha_fin 20260105
```

## Parámetros

### En `process_missing_cierres.py`

Editar la función `main()` para cambiar periodo:

```python
# PASO 1: Buscar cierres faltantes
fecha_ini = "20260101"  # Cambiar aquí
fecha_fin = "20260131"  # Cambiar aquí
```

### Módulos a ejecutar

Por defecto: `['VENTAS', 'MEDIOS_PAGO', 'ANULACIONES']`

Cambiar en `main()`:
```python
modulos = ['VENTAS', 'MEDIOS_PAGO', 'ANULACIONES']  # Editar aquí
```

## Casos de Uso

### Caso 1: Solo ver resumen de faltantes
```bash
python process_missing_cierres.py
```
Verá el resumen pero NO ejecutará nada.

### Caso 2: Ver detalles técnicos
Editar `process_missing_cierres.py` y descomentar prints de debug.

### Caso 3: Ejecutar solo para ciertos locales
```python
# En process_missing_cierres.py:
df_missing = df_missing[df_missing['localid'].isin([1, 2, 3])]  # Solo locales 1, 2, 3
```

## Validaciones Automáticas

El script QA verifica automáticamente:

1. ✓ El cierre existe en geocom
2. ✓ Hay datos de ventas en geocom
3. ✓ Hay datos de medios de pago en geocom
4. ✓ El cierre NO existe en DW (confirmación de faltante)
5. ✓ El detalle del cierre NO existe en DW

**Todos estos deben pasar antes de ir a PROD**

## Seguridad

⚠️ **IMPORTANTE:**
- Los datos se cargan en DW con los comandos generados
- NO se ejecuta `run.py` automáticamente
- Los comandos deben revisarse manualmente antes de ejecutar en PROD
- El script genera un archivo `.sh` con todos los comandos para auditoría

## Troubleshooting

### Error: "No hay cierres en geocom"
- Verificar que las tablas existan y tengan datos
- Verificar credenciales en `.env`

### Error: "Error al consultar geocom"
- Verificar conexión a base de datos geocom
- Verificar que `DB_USER_GEOCOM` y credenciales estén correctas

### Test FAIL: "Cierre NO existe en DW"
- Significa que el cierre ya fue cargado
- No ejecutar para ese cierre

### Test FAIL: "Datos de ventas existen en geocom"
- Cierre sin datos de ventas
- Revisar si es un cierre válido

## Próximas Mejoras

- [ ] Agregar logging a archivo
- [ ] Permitir filtrar por local/POS en parámetros
- [ ] Validar integridad de datos después de cargar
- [ ] Enviar notificaciones por Slack/email
