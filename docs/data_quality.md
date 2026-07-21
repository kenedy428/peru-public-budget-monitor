# Línea base de calidad de datos

## 1. Propósito

Este documento presenta los controles y hallazgos de calidad aplicados a las fuentes oficiales de ejecución presupuestal del Ministerio de Economía y Finanzas utilizadas por Peru Public Budget Monitor.

La línea base permite conocer el estado de los archivos antes de iniciar su transformación, integración, almacenamiento y análisis.

## 2. Fuentes evaluadas

| Fuente | Periodo | Filas | Columnas | Último mes con información |
|---|---:|---:|---:|---|
| `mef_devengado_2024` | 2024 | 2,789,753 | 73 | Diciembre |
| `mef_devengado_2025` | 2025 | 2,807,163 | 73 | Diciembre |
| `mef_devengado_2026` | 2026 | 2,101,712 | 73 | Junio |

En total, se evaluaron 7,698,628 registros.

Los tres recursos presentan la misma cantidad, nombres y orden de columnas, lo que permite su integración posterior bajo un esquema común.

## 3. Controles críticos

### 3.1 Correspondencia del año

Se verificó que el campo `ANO_EJE` corresponda al año configurado para cada fuente.

| Año | Resultado |
|---:|---|
| 2024 | Aprobado |
| 2025 | Aprobado |
| 2026 | Aprobado |

No se detectaron valores nulos, errores de conversión ni años diferentes al periodo esperado.

### 3.2 Reconciliación del monto devengado

Se comprobó que `MONTO_DEVENGADO_ANUAL` coincida con la suma de las doce columnas mensuales, dentro de una tolerancia de 0.01.

| Año | Resultado |
|---:|---|
| 2024 | Aprobado |
| 2025 | Aprobado |
| 2026 | Aprobado |

No se encontraron diferencias superiores a la tolerancia establecida.

### 3.3 Estructura de los archivos

No se encontraron:

- filas vacías;
- filas malformadas;
- diferencias de esquema entre años;
- errores de conversión en las columnas monetarias evaluadas.

## 4. Valores vacíos

No se detectaron valores nulos reales. Sin embargo, se identificaron cadenas vacías o compuestas únicamente por espacios.

Después de analizar su contexto, todos los casos fueron clasificados como vacíos estructurales.

| Año | Vacíos estructurales | Vacíos inesperados |
|---:|---:|---:|
| 2024 | 7,317,342 | 0 |
| 2025 | 7,253,003 | 0 |
| 2026 | 5,229,572 | 0 |

Se aplicaron las siguientes reglas:

1. `SECTOR`, `SECTOR_NOMBRE`, `PLIEGO` y `PLIEGO_NOMBRE` pueden estar vacíos en registros cuyo nivel sea `GOBIERNOS LOCALES`.
2. `META_NOMBRE` puede estar vacío cuando `FINALIDAD` es igual a `99999`.
3. `DEPARTAMENTO_META_NOMBRE` puede estar vacío cuando `DEPARTAMENTO_META` es igual a `0`.

Estos casos se registran como hallazgos informativos y no como errores de calidad.

## 5. Montos negativos

Se evaluaron las 18 columnas cuyo nombre comienza con `MONTO_`.

| Año | Valores negativos | Estado |
|---:|---:|---|
| 2024 | 90,238 | Advertencia |
| 2025 | 91,402 | Advertencia |
| 2026 | 18,759 | Advertencia |

Los montos negativos se conservan porque pueden representar ajustes, anulaciones, regularizaciones o reversos presupuestales.

No se eliminan ni convierten automáticamente a cero. Su interpretación deberá realizarse considerando las reglas de negocio y el contexto presupuestal.

## 6. Filas completamente duplicadas

Se calcularon hashes SHA-256 sobre la totalidad de los campos de cada fila.

| Año | Filas | Filas únicas | Duplicados adicionales | Grupos duplicados |
|---:|---:|---:|---:|---:|
| 2024 | 2,789,753 | 2,789,751 | 2 | 2 |
| 2025 | 2,807,163 | 2,807,153 | 10 | 10 |
| 2026 | 2,101,712 | 2,101,712 | 0 | 0 |

La máxima frecuencia observada fue de dos apariciones por grupo.

Los duplicados de 2024 y 2025 corresponden a registros con montos presupuestales iguales a cero. Las filas originales se mantienen intactas en la capa `raw`.

Su eventual deduplicación se evaluará durante la transformación, sin modificar los archivos oficiales descargados.

## 7. Resultado general

La línea base obtuvo los siguientes resultados:

- cero controles críticos fallidos;
- correspondencia correcta del año;
- reconciliación correcta del devengado anual;
- esquemas equivalentes entre 2024, 2025 y 2026;
- ausencia de valores nulos reales;
- ausencia de vacíos inesperados;
- ausencia de filas malformadas;
- montos negativos registrados como advertencias;
- duplicados completos identificados y documentados.

Los archivos son aptos para continuar con la etapa de definición del grano, transformación y construcción del modelo analítico.

## 8. Ejecución de los controles

Validación general:

```bash
python -m src.validate_quality \
  --all \
  --chunk-rows 100000 \
  --tolerance 0.01