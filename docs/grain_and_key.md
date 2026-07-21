# Definición del grano y clave de consolidación

## 1. Propósito

Este documento define el nivel de detalle de los datos de ejecución presupuestal utilizados por Peru Public Budget Monitor y presenta la validación de la clave candidata empleada para consolidar los registros oficiales del Ministerio de Economía y Finanzas.

La definición del grano se realiza antes de transformar, integrar y cargar los datos en PostgreSQL.

## 2. Fuentes analizadas

| Fuente | Periodo | Filas originales | Columnas |
|---|---:|---:|---:|
| `mef_devengado_2024` | 2024 | 2,789,753 | 73 |
| `mef_devengado_2025` | 2025 | 2,807,163 | 73 |
| `mef_devengado_2026` | 2026 | 2,101,712 | 73 |
| **Total** |  | **7,698,628** |  |

Los tres archivos presentan la misma cantidad, nombres y orden de columnas.

## 3. Clasificación de las columnas

Las 73 columnas se distribuyen en:

- 18 medidas monetarias;
- 25 campos descriptivos;
- 30 códigos o posibles dimensiones.

Las medidas monetarias comprenden:

- presupuesto institucional de apertura;
- presupuesto institucional modificado;
- certificado anual;
- comprometido anual;
- devengado mensual de enero a diciembre;
- devengado anual;
- girado anual.

## 4. Definición del grano

El grano analítico provisional se define como:

> Una fila por combinación única de año, unidad ejecutora, estructura programática, meta presupuestaria, finalidad, ubicación de la meta, fuente de financiamiento, rubro, tipo de recurso y clasificador de gasto.

Las medidas monetarias correspondientes a una misma combinación se consolidan en una sola fila.

## 5. Clave de consolidación

La clave candidata validada se denomina `business_key_v1` y contiene 24 columnas:

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

Esta clave se utilizará para agrupar los registros durante la transformación.

## 6. Atributos excluidos de la clave

La clave técnica máxima evaluada contenía también:

- `NIVEL_GOBIERNO`;
- `SECTOR`;
- `PLIEGO`;
- `DEPARTAMENTO_EJECUTORA`;
- `PROVINCIA_EJECUTORA`;
- `DISTRITO_EJECUTORA`.

La clave técnica de 30 columnas y `business_key_v1` produjeron exactamente la misma cantidad de combinaciones y colisiones.

Por tanto, esos seis campos no aportaron unicidad adicional en los archivos evaluados. Se conservarán como atributos descriptivos o jerárquicos, pero no formarán parte de la clave de consolidación.

## 7. Concepto de colisión

Una colisión de clave ocurre cuando dos o más filas presentan la misma combinación de valores en todas las columnas de la clave candidata, aunque alguna columna restante tenga un valor diferente.

No se trata de una colisión criptográfica de SHA-256. El hash se utiliza únicamente para representar y comparar eficientemente la combinación de columnas.

Una colisión puede indicar:

- una clave incompleta;
- atributos descriptivos inconsistentes;
- medidas monetarias distribuidas entre varias filas;
- o filas completamente duplicadas.

## 8. Resultados

| Año | Filas originales | Claves únicas | Grupos en colisión | Filas adicionales | Máxima repetición |
|---:|---:|---:|---:|---:|---:|
| 2024 | 2,789,753 | 2,789,605 | 148 | 148 | 2 |
| 2025 | 2,807,163 | 2,807,021 | 142 | 142 | 2 |
| 2026 | 2,101,712 | 2,101,614 | 98 | 98 | 2 |
| **Total** | **7,698,628** | **7,698,240** | **388** | **388** |  |

Los 388 grupos contienen exactamente dos filas cada uno, por lo que existen 776 filas involucradas.

Después de la consolidación se esperan 7,698,240 filas.

La reducción respecto de los archivos originales es de aproximadamente 0.005040 %.

## 9. Validación de las colisiones

Se exportaron y revisaron todas las filas pertenecientes a los grupos en colisión:

| Año | Grupos revisados | Filas revisadas |
|---:|---:|---:|
| 2024 | 148 | 296 |
| 2025 | 142 | 284 |
| 2026 | 98 | 196 |
| **Total** | **388** | **776** |

En los tres años se comprobó que:

- no existen diferencias en columnas no monetarias dentro de los grupos;
- todos los grupos contienen exactamente dos filas;
- ninguna medida monetaria presenta más de una fila con un valor distinto de cero dentro del mismo grupo;
- la consolidación no duplica valores monetarios existentes.

Las diferencias se concentran en:

- `MONTO_PIM`;
- `MONTO_CERTIFICADO_ANUAL`;
- `MONTO_COMPROMETIDO_ANUAL`.

La fuente puede distribuir estas medidas entre filas distintas correspondientes a la misma combinación presupuestal.

## 10. Regla de transformación

Durante la transformación se aplicará la siguiente regla:

1. Agrupar por las 24 columnas de `business_key_v1`.
2. Sumar las 18 columnas monetarias.
3. Conservar los atributos descriptivos asociados a la combinación.
4. Validar que los atributos no monetarios sean consistentes dentro de cada grupo.
5. Comparar los totales monetarios antes y después de la consolidación.
6. Mantener intactos los archivos oficiales de la capa `raw`.

La suma de las medidas es segura porque no se detectaron valores distintos de cero superpuestos para una misma medida dentro de los grupos evaluados.

## 11. Consideraciones

`business_key_v1` ha sido validada como clave de consolidación para los archivos 2024, 2025 y 2026 utilizados por el MVP.

La validación demuestra que la clave produce un grano consistente, pero no necesariamente que sea la combinación mínima matemáticamente posible.

Una futura iteración podría analizar dependencias funcionales y eliminar campos redundantes. Esta optimización no es necesaria para garantizar la correcta consolidación actual.

## 12. Reproducción del análisis

Ejemplo para una fuente:

```bash
python -m src.analyze_grain \
  --source-id mef_devengado_2026 \
  --batch-rows 50000 \
  --sample-limit 1000 \
  --sample-key business_key_v1