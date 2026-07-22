# Transformación y consolidación de datos del MEF

## 1. Propósito

Este documento describe el proceso reproducible utilizado para transformar y consolidar las fuentes oficiales de ejecución presupuestal del Ministerio de Economía y Finanzas correspondientes a los años 2024, 2025 y 2026.

La transformación genera una capa procesada preparada para su posterior carga en PostgreSQL, conservando intactos los archivos oficiales almacenados en `data/raw/`.

## 2. Fuentes procesadas

| Fuente | Periodo | Filas originales |
|---|---:|---:|
| `mef_devengado_2024` | 2024 | 2,789,753 |
| `mef_devengado_2025` | 2025 | 2,807,163 |
| `mef_devengado_2026` | 2026 | 2,101,712 |
| **Total** |  | **7,698,628** |

Cada archivo contiene 73 columnas y presenta el mismo esquema.

## 3. Objetivos de la transformación

El proceso implementado permite:

- normalizar valores textuales;
- convertir las medidas monetarias a valores numéricos;
- detectar valores monetarios no válidos;
- eliminar filas completamente duplicadas;
- consolidar registros mediante `business_key_v1`;
- sumar las 18 columnas monetarias;
- conservar los atributos no monetarios;
- detectar inconsistencias dentro de una misma clave;
- verificar los totales monetarios antes y después de la consolidación;
- generar archivos CSV procesados;
- generar reportes JSON de reconciliación.

## 4. Grano y clave de consolidación

El grano analítico se define como una fila por combinación única de:

- año;
- unidad ejecutora;
- estructura programática;
- meta presupuestaria;
- finalidad;
- ubicación de la meta;
- fuente de financiamiento;
- rubro;
- tipo de recurso;
- clasificador de gasto.

La consolidación utiliza la clave `business_key_v1`, formada por las siguientes 24 columnas:

1. `ANO_EJE`
2. `SEC_EJEC`
3. `EJECUTORA`
4. `PROGRAMA_PPTO`
5. `TIPO_ACT_PROY`
6. `PRODUCTO_PROYECTO`
7. `ACTIVIDAD_ACCION_OBRA`
8. `FUNCION`
9. `DIVISION_FUNCIONAL`
10. `GRUPO_FUNCIONAL`
11. `SEC_FUNC`
12. `META`
13. `FINALIDAD`
14. `DEPARTAMENTO_META`
15. `FUENTE_FINANCIAMIENTO`
16. `RUBRO`
17. `TIPO_RECURSO`
18. `CATEGORIA_GASTO`
19. `TIPO_TRANSACCION`
20. `GENERICA`
21. `SUBGENERICA`
22. `SUBGENERICA_DET`
23. `ESPECIFICA`
24. `ESPECIFICA_DET`

## 5. Medidas monetarias

Se identifican como medidas todas las columnas cuyo nombre comienza con `MONTO_`.

La transformación consolida 18 medidas:

- `MONTO_PIA`
- `MONTO_PIM`
- `MONTO_CERTIFICADO_ANUAL`
- `MONTO_COMPROMETIDO_ANUAL`
- `MONTO_DEVENGADO_ENERO`
- `MONTO_DEVENGADO_FEBRERO`
- `MONTO_DEVENGADO_MARZO`
- `MONTO_DEVENGADO_ABRIL`
- `MONTO_DEVENGADO_MAYO`
- `MONTO_DEVENGADO_JUNIO`
- `MONTO_DEVENGADO_JULIO`
- `MONTO_DEVENGADO_AGOSTO`
- `MONTO_DEVENGADO_SEPTIEMBRE`
- `MONTO_DEVENGADO_OCTUBRE`
- `MONTO_DEVENGADO_NOVIEMBRE`
- `MONTO_DEVENGADO_DICIEMBRE`
- `MONTO_DEVENGADO_ANUAL`
- `MONTO_GIRADO_ANUAL`

## 6. Normalización

Antes de consolidar los datos se aplican las siguientes reglas:

1. Los espacios ubicados al inicio y al final de los textos son eliminados.
2. Las cadenas vacías o formadas únicamente por espacios se convierten en valores nulos.
3. Las columnas monetarias se convierten a valores numéricos.
4. Los valores monetarios vacíos se interpretan como cero.
5. Los valores no vacíos que no puedan convertirse a número provocan el rechazo de la transformación.

## 7. Procesamiento por bloques

Los archivos se leen en bloques de 50,000 filas para limitar el consumo de memoria RAM.

El proceso muestra avances cada cinco bloques, equivalentes aproximadamente a 250,000 filas:

```text
bloques=5 | filas procesadas=250,000
bloques=10 | filas procesadas=500,000
```


## 8. Duplicados exactos

Una fila se considera duplicada exacta cuando coinciden sus 73 columnas.

Antes de consolidar por la clave de negocio, el proceso calcula un hash SHA-256 de la fila completa y conserva una sola aparición de cada registro idéntico.

Resultados:

| Año | Duplicados exactos eliminados |
|---:|---:|
| 2024 | 2 |
| 2025 | 10 |
| 2026 | 0 |
| **Total** | **12** |

## 9. Consolidación por clave

Después de eliminar los duplicados exactos, los registros que comparten `business_key_v1` se consolidan:

- los atributos no monetarios deben coincidir;
- las medidas monetarias se suman;
- cualquier diferencia no monetaria provoca el rechazo del proceso.

Resultados:

| Año | Filas consolidadas por clave |
|---:|---:|
| 2024 | 146 |
| 2025 | 132 |
| 2026 | 98 |
| **Total** | **376** |

No se encontraron grupos con atributos no monetarios inconsistentes.

## 10. Resultados finales

| Año | Filas originales | Duplicados exactos | Filas agrupadas | Filas finales |
|---:|---:|---:|---:|---:|
| 2024 | 2,789,753 | 2 | 146 | 2,789,605 |
| 2025 | 2,807,163 | 10 | 132 | 2,807,021 |
| 2026 | 2,101,712 | 0 | 98 | 2,101,614 |
| **Total** | **7,698,628** | **12** | **376** | **7,698,240** |

En total se retiraron 388 filas:

```text
12 duplicados exactos
+ 376 filas consolidadas por clave
= 388 filas retiradas
```

La reducción representa aproximadamente el 0.005040 % de los registros originales.

## 11. Reconciliación monetaria

El proceso calcula los totales de cada medida monetaria antes y después de la consolidación.

Los reportes contienen dos tipos de diferencias:

### Diferencias técnicas

`raw_measure_total_differences` registra el residuo técnico producido por la representación binaria de números decimales mediante valores de punto flotante.

Estas diferencias pueden contener cantidades muy pequeñas, como:

```text
-0.0086669922
0.0035095215
```

### Diferencias monetarias

`measure_total_differences` compara los totales a una precisión monetaria de dos decimales.

La transformación utiliza una tolerancia máxima de S/ 0.01.

Los tres periodos obtuvieron:

```text
totals_preserved = true
```

Por tanto, no se detectaron pérdidas monetarias relevantes durante la consolidación.

Para la capa PostgreSQL se utilizará un tipo decimal exacto, como `NUMERIC`, en lugar de valores binarios de punto flotante.

## 12. Archivos generados

Los archivos consolidados se almacenan localmente en:

```text
data/processed/
```

Archivos principales:

```text
mef_devengado_2024_consolidated.csv
mef_devengado_2025_consolidated.csv
mef_devengado_2026_consolidated.csv
```

También se genera un reporte JSON por ejecución:

```text
*_mef_devengado_2024_transform_report.json
*_mef_devengado_2025_transform_report.json
*_mef_devengado_2026_transform_report.json
```

Los archivos procesados y reportes están excluidos de Git debido a su tamaño y porque pueden reproducirse desde los archivos oficiales.

El conjunto procesado ocupa aproximadamente 6.3 GB.

## 13. Tiempos observados

Los tiempos dependen del procesador, la memoria disponible, el disco, el antivirus y otras aplicaciones abiertas.

En el entorno de desarrollo actual se observaron aproximadamente:

| Año | Duración aproximada |
|---:|---:|
| 2024 | 1 hora y 18 minutos |
| 2025 | 1 hora y 13 minutos |
| 2026 | 1 hora y 45 minutos |

Estas mediciones incluyen:

- lectura y normalización;
- cálculo de hashes;
- consolidación en SQLite;
- reconciliación monetaria;
- escritura del CSV final.

## 14. Reproducción

Ejemplo para transformar 2024:

```bash
python -m src.transform \
  --source-id mef_devengado_2024 \
  --chunk-rows 50000 \
  --tolerance 0.01
```

Para transformar todos los periodos:

```bash
python -m src.transform \
  --all \
  --chunk-rows 50000 \
  --tolerance 0.01
```

Debido al tiempo requerido, se recomienda procesar los periodos individualmente.

## 15. Pruebas automatizadas

La transformación cuenta con pruebas para:

- identificación de medidas monetarias;
- normalización de textos;
- consolidación de medidas distribuidas;
- eliminación de duplicados exactos;
- detección de atributos inconsistentes;
- rechazo de montos no numéricos;
- consolidación entre bloques diferentes;
- generación de archivos y reportes;
- reconciliación a precisión monetaria.

Resultado final:

```text
46 passed
```

## 16. Estado de validación

Los tres periodos obtuvieron estado aprobado:

- cantidades originales correctas;
- cantidades finales correctas;
- duplicados exactos esperados;
- consolidaciones esperadas;
- cero grupos inconsistentes;
- totales monetarios preservados;
- archivos procesados existentes;
- bases SQLite temporales eliminadas.

La capa procesada queda lista para el diseño y carga de PostgreSQL.