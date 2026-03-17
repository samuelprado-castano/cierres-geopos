# Quick Start - Cierres Faltantes

## ⚡ En 30 segundos

```bash
# 0. Verificar conexiones (hacer primero!)
python test_connection.py

# 1. Ejecutar análisis completo
python process_missing_cierres.py

# 2. Revisar reporte QA
cat qa_missing_cierres.csv

# 3. Si todo OK, ejecutar en PROD (cuando sea aprobado)
bash missing_cierres_commands.sh
```

---

## 📊 Qué hace cada comando

### `python process_missing_cierres.py`

Encuentra los 173 cierres de enero 2026 que faltan en DW:

**Módulos que procesa:** TODOS (VENTAS, MEDIOS_PAGO, REDONDEOS, DEPOSITOS, GUIAS)
*(Si quieres específicos, edita el archivo y define la lista de módulos)*

```
📊 RESUMEN DEL PERÍODO 20260101-20260131:
   - Cierres en geocom.totals: 300
   - Cierres en DW.cierres: 127
   - Cierres faltantes: 173 ✓
```

✓ Valida cada cierre (QA automático)
✓ Genera comandos para ejecutar en PROD
✓ NO ejecuta nada aún

**Salida:**
- `qa_missing_cierres.csv` - Reporte de validaciones
- `missing_cierres_commands.sh` - 173 comandos para ejecutar

---

## 🔍 Validaciones Automáticas (QA)

Para cada cierre faltante, valida:

| ✓ | Validación | Debe ser |
|---|-----------|----------|
| 1 | Existe en geocom.totals | PASS |
| 2 | Hay ventas en geocom | PASS (o WARNING si no hay) |
| 3 | Hay medios de pago en geocom | PASS (o WARNING si no hay) |
| 4 | NO existe en DW.cierres | PASS |
| 5 | NO existe en DW.cierres_detalle | PASS |

❌ Si alguno es **FAIL**: no proceder a PROD

---

## 📁 Archivos Generados

```
cierres-geopos/
├── qa_missing_cierres.csv           ← Revisar esto
├── missing_cierres_commands.sh       ← Ejecutar esto en PROD
├── process_missing_cierres.py        ← Script principal
├── src/
│   ├── missing_cierres.py
│   └── qa_missing_cierres.py
└── README_MISSING_CIERRES.md         ← Documentación completa
```

---

## 🚀 Ejecución en PROD

Cuando todo esté aprobado:

```bash
# Ver los comandos (opcional)
cat missing_cierres_commands.sh

# Ejecutar todos (cada comando procesa 1 cierre)
bash missing_cierres_commands.sh

# O ejecutar uno por uno para monitorear
python run.py --modulos VENTAS MEDIOS_PAGO ANULACIONES \
  --localid 1 --pos 1 --fecha_ini 20260105 --fecha_fin 20260105
```

---

## ❌ Si hay errores

### Test FAIL: "Cierre NO existe en DW"
→ El cierre ya fue cargado, no procesar

### Test FAIL: "Datos de ventas existen en geocom"
→ Cierre sin datos, revisar si es válido

### Error de conexión
→ Verificar credenciales en `.env`

### Generó 0 cierres faltantes
→ ✓ Todos ya fueron cargados

---

## 🎯 Resumen del Período

**Enero 2026 (01/01 a 01/31):**
- Total en geocom: 300 cierres
- Cargados en DW: 127 cierres
- Faltantes: **173 cierres** ← A procesar

---

## 📞 Comandos Útiles

```bash
# Ver resumen rápido
python process_missing_cierres.py | head -50

# Revisar un cierre específico (Local 1, POS 1, 05-01-2026)
python run.py --modulos VENTAS --localid 1 --pos 1 \
  --fecha_ini 20260105 --fecha_fin 20260105

# Explorar manualmente
python example_manual_usage.py

# Contar cuántos comandos se van a ejecutar
wc -l missing_cierres_commands.sh
```

---

## ✅ Checklist Antes de PROD

- [ ] Ejecuté `python process_missing_cierres.py`
- [ ] Revisé `qa_missing_cierres.csv`
- [ ] Todos los tests son ✓ PASS
- [ ] Aprobé los 173 cierres a procesar
- [ ] Ejecuté `bash missing_cierres_commands.sh` o los comandos uno a uno
- [ ] Verifiqué que los cierres estén en DW

---

## 📚 Para Más Información

- [README_MISSING_CIERRES.md](README_MISSING_CIERRES.md) - Documentación completa
- [ESTRUCTURA_CIERRES_FALTANTES.txt](ESTRUCTURA_CIERRES_FALTANTES.txt) - Diagrama del flujo
- [example_manual_usage.py](example_manual_usage.py) - Ejemplos de código
