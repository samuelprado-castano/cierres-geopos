# CLAUDE.md - Instrucciones del Proyecto GeoPOS Cierres

## Contexto del Proyecto

**Proyecto:** GeoPOS - Sistema de Carga de Cierres de Caja
**Estado:** LISTO PARA PRODUCCIÓN (Marzo 2026)
**Riesgo:** BAJO - Con todas las protecciones implementadas
**Período:** Análisis desde 2026-01-01 a 2026-03-15

## Reglas del Proyecto

- **SIN EMOJIS**: No usar símbolos emoji en commits, documentación o comentarios de código
- **Append-Only Mode**: NUNCA borrar datos existentes, NUNCA reemplazar tablas - Solo insertar nuevos registros
- **Máxima Granularidad**: Usar (localid + pos + z + closed) como clave única, no solo (localid + pos + z)
- **Deduplicación Automática**: El sistema detecta Z duplicados por reinicio y agrega fechas automáticamente
- **Documentación Técnica**: Consultar `documentacion.md` para especificaciones detalladas
- **Historial de Cambios**: Consultar `CHANGES.md` para decisiones técnicas implementadas

## Operación Diaria (11 PM - Principal)

### Ejecución Automática del ETL

**Horario:** 23:00 (11 PM) todos los días
**Comando:**
```bash
python run.py REDONDEOS MEDIOS_PAGO VENTAS DEPOSITOS GUIAS
```

**Qué hace:**
1. Procesa TODOS los cierres de HOY
2. Desde TODAS las tiendas
3. Desde TODOS los POS
4. Carga en DW automáticamente con protecciones de deduplicación
5. Genera log de ejecución

**Configuración:** Ver cron/scheduler del servidor

---

## Operación Excepcional - Cierres Faltantes

### Cuando Se Detectan Cierres Faltantes

Si por algún motivo se detectan cierres que no fueron cargados en el ETL diario:

```bash
# 1. Analizar cierres faltantes
python process_missing_cierres.py

# 2. Revisar validaciones
cat output/qa_missing_cierres.csv

# 3. Ejecutar carga de faltantes (si está OK)
bash output/missing_cierres_commands.sh
```

---

## Verificación Inicial

```bash
python test_connection.py
```

Valida que las conexiones a GeoCom y DW estén funcionando correctamente.

## Estructura de Carpetas

```
.
├── CLAUDE.md                      # Este archivo - Instrucciones
├── README.md                      # Descripción general del proyecto
├── CHANGES.md                     # Historial de cambios técnicos
├── documentacion.md               # Especificación técnica completa
├── src/
│   ├── main.py                   # ETL principal
│   ├── missing_cierres.py        # Búsqueda de cierres faltantes
│   ├── qa_missing_cierres.py     # Validaciones QA (8 tests)
│   └── db_config.py              # Configuración de bases de datos
├── logs/                         # Logs de ejecución
├── output/                       # Reportes y CSV (cierres_faltantes.csv, qa_missing_cierres.csv)
└── run.py                        # Punto de entrada principal
```

## Flujo de Operación Normal (ETL Diario)

### 1. Ejecución Automática (11 PM - Todos los Días)

```bash
python run.py REDONDEOS MEDIOS_PAGO VENTAS DEPOSITOS GUIAS
```

- Procesa todos los cierres de HOY
- Todas las tiendas, todos los POS
- Carga automáticamente en DW
- Con validación de duplicados integrada
- Registra resultado en logs/

### 2. Validación (Manual - Si Necesario)

Si hay dudas sobre cierres o se detectan faltantes:

```bash
python process_missing_cierres.py
```

- Identifica cierres faltantes
- Ejecuta 8 validaciones QA
- Detecta automáticamente Z duplicados

### 3. Revisión de Resultados

```bash
cat output/qa_missing_cierres.csv
```

- Valida status de cada cierre
- Revisa advertencias o errores

### 4. Carga de Faltantes (Si Hay)

```bash
bash output/missing_cierres_commands.sh
```

- Solo si se detectaron cierres faltantes
- Con deduplicación automática
- Después de revisión manual

## Conceptos Clave

### Z Number (Znumber)
- Contador de cierres en una caja registradora
- **SE REINICIA PERIÓDICAMENTE** (cada 100-1000 transacciones)
- No es globalmente único: se repite entre locales y después de reinicio
- **Clave única real:** (localid + pos + z + closed)

### Deduplicación por Fecha
Cuando Z se repite, el sistema automáticamente:
1. Detecta el reinicio
2. Agrega --fecha_ini y --fecha_fin
3. Filtra por (localid + pos + z + closed_exacto)
4. Procesa exactamente UN cierre

### Validaciones QA
8 tests automáticos por cierre:
1. Existe en GeoCom
2. Hay ventas asociadas
3. Hay medios de pago
4. No existe en DW (deduplicación)
5. Detalle no existe en DW
6. Consistencia cabecera-detalle
7. Sin datos huérfanos
8. Detecta Z duplicados

## Modo Uso

### Opción 1: Por Z Number (Recomendado)
```bash
python run.py --modulos VENTAS --localid 333 --pos 1 --z 1
```
- Procesa exactamente UN cierre específico
- Mayor precisión, menor riesgo

### Opción 2: Por Rango de Fechas
```bash
python run.py --modulos VENTAS --fecha_ini 20260310 --fecha_fin 20260312
```
- Procesa todos los cierres en ese rango
- Útil cuando no conoces el Z

### Opción 3: Con Deduplicación Manual
```bash
python run.py --modulos VENTAS --localid 333 --pos 1 --z 1 --fecha_ini 20260311 --fecha_fin 20260311
```
- Especifica fecha exacta para desambiguar Z duplicado
- Automático si se detecta duplicado

## Archivos Importantes

- **src/main.py**: ETL con validación dual (cabecera + detalle)
- **src/missing_cierres.py**: Query de cierres faltantes
- **src/qa_missing_cierres.py**: 8 validaciones QA
- **process_missing_cierres.py**: Orquestador principal
- **missing_cierres_commands.sh**: Comandos generados para PROD

## Contacto y Documentación

Para detalles técnicos profundos, ver `documentacion.md`.
Para cambios implementados, ver `CHANGES.md`.
Para README general, ver `README.md`.

---

**Última actualización:** 2026-03-20
**Status:** LISTO PARA PRODUCCIÓN
