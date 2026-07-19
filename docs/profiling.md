# Perfilado de fuentes oficiales del MEF

## 1. Propósito

Este documento describe el proceso reproducible utilizado para inspeccionar y comparar la estructura y el contenido básico de los archivos oficiales del MEF correspondientes a 2024, 2025 y 2026.

El perfilado fue diseñado para trabajar con archivos de varios gigabytes sin cargarlos completamente en memoria.

---

## 2. Fuentes perfiladas

| Año | Recurso |
|---|---|
| 2024 | `2024-Gasto-Devengado.csv` |
| 2025 | `2025-Gasto-Devengado-Mensual.csv` |
| 2026 | `2026-Gasto-Devengado-Mensual.csv` |

También se utilizó el diccionario oficial:

```text
Gasto_Devengado_Diccionario.csv
```

---

## 3. Componentes implementados

### Perfilado ligero

El módulo:

```text
src/profile_sources.py
```

permite:

- leer la cabecera de cada CSV;
- utilizar una muestra configurable de filas;
- registrar nombres y orden de columnas;
- inferir tipos preliminares desde una muestra;
- contar valores nulos dentro de la muestra;
- comparar las columnas reales con el diccionario oficial;
- identificar columnas no documentadas;
- identificar variables del diccionario ausentes en los archivos;
- separar las columnas mensuales y anuales de Devengado;
- comparar automáticamente los esquemas de 2024, 2025 y 2026;
- generar reportes JSON individuales y consolidados.

### Escaneo por bloques

El módulo:

```text
src/scan_sources.py
```

permite:

- procesar los archivos completos por bloques;
- contar filas reales sin cargar todo el dataset en memoria;
- contabilizar nulos, ceros y valores distintos de cero por mes;
- determinar el último mes con información efectiva;
- generar un reporte JSON por fuente.

---

## 4. Ejecutar el perfilado ligero

### Perfilar 2026

```bash
python -m src.profile_sources \
  --source-id mef_devengado_2026 \
  --sample-rows 1000
```

### Perfilar los tres años

```bash
python -m src.profile_sources \
  --all \
  --sample-rows 1000
```

Cuando se perfilan varias fuentes, se genera automáticamente un reporte consolidado de comparación de esquemas.

---

## 5. Ejecutar el escaneo completo

### Escanear una fuente

```bash
python -m src.scan_sources \
  --source-id mef_devengado_2026 \
  --chunk-rows 100000
```

### Escanear todas las fuentes

```bash
python -m src.scan_sources \
  --all \
  --chunk-rows 100000
```

El parámetro `--chunk-rows` determina cuántas filas se procesan simultáneamente.

El uso de bloques permite recorrer archivos de varios gigabytes manteniendo un consumo de memoria controlado.

---

## 6. Resultados estructurales

Los tres archivos presentan:

| Validación | Resultado |
|---|---|
| Cantidad de columnas | 73 |
| Mismos nombres de columnas | Sí |
| Mismo orden de columnas | Sí |
| Columnas no documentadas | 0 |
| Variables del diccionario ausentes | 0 |
| Columnas faltantes respecto a 2024 | 0 |
| Columnas adicionales respecto a 2024 | 0 |

Por tanto, los archivos 2024, 2025 y 2026 son estructuralmente compatibles.

Esta compatibilidad no implica todavía que puedan concatenarse sin validaciones adicionales. Antes deberán revisarse los tipos efectivos, el grano, los identificadores y las reglas de calidad.

---

## 7. Columnas de Devengado

Se identificaron 13 columnas relacionadas con el monto devengado.

### Columnas mensuales

```text
MONTO_DEVENGADO_ENERO
MONTO_DEVENGADO_FEBRERO
MONTO_DEVENGADO_MARZO
MONTO_DEVENGADO_ABRIL
MONTO_DEVENGADO_MAYO
MONTO_DEVENGADO_JUNIO
MONTO_DEVENGADO_JULIO
MONTO_DEVENGADO_AGOSTO
MONTO_DEVENGADO_SEPTIEMBRE
MONTO_DEVENGADO_OCTUBRE
MONTO_DEVENGADO_NOVIEMBRE
MONTO_DEVENGADO_DICIEMBRE
```

### Columna anual

```text
MONTO_DEVENGADO_ANUAL
```

La columna anual deberá validarse posteriormente contra la suma de los doce montos mensuales.

---

## 8. Cantidad de filas

El escaneo completo obtuvo:

| Año | Filas | Bloques procesados |
|---|---:|---:|
| 2024 | 2,789,753 | 28 |
| 2025 | 2,807,163 | 29 |
| 2026 | 2,101,712 | 22 |

Los bloques utilizados fueron de 100,000 filas.

---

## 9. Cobertura mensual

El último mes con al menos un monto Devengado distinto de cero fue:

| Año | Último mes poblado |
|---|---|
| 2024 | Diciembre |
| 2025 | Diciembre |
| 2026 | Junio |

### Hallazgo sobre 2026

Las columnas de julio a diciembre de 2026 existen y contienen valores no nulos, pero todos los registros presentan monto cero.

Por este motivo, la disponibilidad mensual no debe determinarse únicamente mediante valores no nulos.

La regla utilizada es:

> El último mes disponible es la última columna mensual que contiene al menos un monto distinto de cero.

Con esta regla, el último periodo con información efectiva de 2026 es junio.

---

## 10. Tipos de datos preliminares

Los tipos registrados por `src/profile_sources.py` se infieren a partir de una muestra configurable.

Estos tipos son preliminares porque:

- una muestra puede no contener todos los valores posibles;
- una columna aparentemente entera puede contener decimales posteriormente;
- los valores nulos pueden modificar la inferencia de pandas;
- los códigos numéricos podrían requerir tratamiento como texto;
- los tipos definitivos deberán establecerse mediante reglas explícitas.

No se utilizarán directamente los tipos inferidos por la muestra para definir el esquema final de PostgreSQL.

---

## 11. Reportes generados

Los resultados se almacenan localmente en:

```text
data/profiling/
```

Los principales reportes son:

```text
*_profile.json
*_schema_comparison.json
*_content_scan.json
```

Los reportes generados están excluidos de GitHub mediante `.gitignore`.

Solo se versionan:

- el código que los genera;
- las pruebas automatizadas;
- la metodología;
- los hallazgos consolidados en esta documentación.

---

## 12. Pruebas automatizadas

Las pruebas relacionadas con el perfilado se encuentran en:

```text
tests/test_profile_sources.py
tests/test_scan_sources.py
```

Validan:

- clasificación de columnas mensuales y anuales;
- igualdad de esquemas;
- diferencias de orden;
- columnas faltantes y adicionales;
- conteo de filas por bloques;
- conteo de nulos;
- detección del último mes poblado;
- comportamiento cuando todos los meses contienen cero.

Todas las pruebas del proyecto pueden ejecutarse mediante:

```bash
python -m pytest -v
```

---

## 13. Cautelas

- La compatibilidad estructural no garantiza compatibilidad semántica.
- Los tipos inferidos a partir de muestras no son definitivos.
- Un valor cero puede representar ausencia de ejecución y no un dato faltante.
- La presencia de columnas futuras no implica que esos meses estén disponibles.
- La columna anual deberá reconciliarse con las columnas mensuales.
- La cantidad de filas no representa necesariamente entidades únicas.
- El grano real deberá determinarse mediante el análisis de las dimensiones y clasificadores.