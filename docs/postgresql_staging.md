# Capa staging en PostgreSQL

## 1. Propósito

Este documento describe la configuración, creación, carga y validación de la capa `staging` de PostgreSQL para los datos consolidados de ejecución presupuestal del MEF correspondientes a 2024, 2025 y 2026.

La capa `staging` recibe los archivos generados por el proceso de transformación y conserva su estructura antes de construir el modelo analítico.

## 2. Entorno utilizado

- PostgreSQL 18.3
- Base de datos: `peru_public_budget`
- Usuario del proyecto: `budget_app`
- Host local: `127.0.0.1`
- Puerto: `5432`

Las credenciales reales se almacenan únicamente en el archivo local `.env`, excluido de Git.

La plantilla pública se encuentra en:

```text
.env.example
```

## 3. Esquemas

Se crearon dos esquemas:

### `staging`

Zona de recepción y validación de los archivos consolidados del MEF.

### `analytics`

Zona reservada para el posterior modelo dimensional, indicadores y consultas destinadas a Power BI.

El script correspondiente es:

```text
sql/001_create_schemas.sql
```

## 4. Tabla staging

La tabla principal es:

```text
staging.mef_devengado
```

Contiene 73 columnas:

- 1 columna de año;
- 18 medidas monetarias;
- 54 columnas de códigos y descripciones.

Los tipos principales son:

| Tipo de dato | Uso |
|---|---|
| `SMALLINT` | Año de ejecución |
| `NUMERIC(24,2)` | Medidas monetarias |
| `TEXT` | Códigos, dimensiones y descripciones |

Los códigos se almacenan como texto para conservar ceros iniciales, por ejemplo:

```text
001
025
0000576
```

La definición de la tabla está versionada en:

```text
sql/002_create_staging_table.sql
```

## 5. Precisión monetaria

Las 18 columnas cuyo nombre comienza con `MONTO_` utilizan:

```sql
NUMERIC(24, 2)
```

A diferencia de los valores binarios de punto flotante, `NUMERIC` representa los importes decimales de manera exacta.

Antes de certificar la carga se auditó cada valor de los tres CSV procesados mediante centavos enteros.

Resultados:

| Año | Valores con más de dos decimales | Valores que requirieron redondeo |
|---:|---:|---:|
| 2024 | 0 | 0 |
| 2025 | 0 | 0 |
| 2026 | 0 | 0 |

Por tanto, PostgreSQL no tuvo que redondear ningún valor durante la carga.

## 6. Carga masiva

Los archivos se cargaron mediante el comando nativo `COPY` de PostgreSQL.

El script utilizado es:

```text
sql/003_load_staging.sql
```

La carga:

1. elimina el índice temporalmente;
2. vacía la tabla mediante `TRUNCATE`;
3. carga los tres CSV;
4. valida los conteos;
5. crea un índice BRIN por año;
6. actualiza las estadísticas con `ANALYZE`;
7. confirma la transacción mediante `COMMIT`.

Archivos cargados:

```text
data/processed/mef_devengado_2024_consolidated.csv
data/processed/mef_devengado_2025_consolidated.csv
data/processed/mef_devengado_2026_consolidated.csv
```

## 7. Conteos cargados

| Año | Filas cargadas |
|---:|---:|
| 2024 | 2,789,605 |
| 2025 | 2,807,021 |
| 2026 | 2,101,614 |
| **Total** | **7,698,240** |

Los conteos coinciden exactamente con los archivos procesados.

## 8. Índice BRIN

Se creó el índice:

```text
idx_mef_devengado_ano_eje_brin
```

Un índice BRIN almacena resúmenes de rangos físicos de la tabla y ocupa poco espacio.

Es apropiado en este caso porque:

- la tabla es grande;
- los archivos fueron cargados en bloques por año;
- los registros del mismo año están físicamente próximos;
- las consultas iniciales filtran frecuentemente por `ano_eje`.

El índice ocupa aproximadamente 224 KB.

## 9. Tamaño físico

Después de la carga se obtuvo aproximadamente:

| Elemento | Tamaño |
|---|---:|
| Tabla | 6,972 MB |
| Índices | 224 KB |
| Total | 6,973 MB |

Los archivos procesados permanecen fuera de Git debido a su tamaño y porque pueden reproducirse.

## 10. Validaciones de staging

El script:

```text
sql/004_validate_staging.sql
```

comprueba:

- conteos por año;
- cantidad total de registros;
- año mínimo y máximo;
- ausencia de años inesperados;
- ausencia de montos nulos;
- tamaño físico de tabla e índices.

Resultados:

```text
total_rows = 7698240
minimum_year = 2024
maximum_year = 2026
unexpected_year_rows = 0
rows_with_null_amounts = 0
```

## 11. Reconciliación monetaria exacta

La auditoría monetaria se implementó en:

```text
src/audit_processed_amounts.py
```

Este módulo:

- lee cada CSV sin utilizar `float`;
- convierte los importes a centavos enteros;
- detecta decimales adicionales;
- identifica valores que requieren redondeo;
- genera totales exactos por columna.

Los totales esperados se comparan con PostgreSQL mediante:

```text
sql/005_validate_amount_totals.sql
```

Se validaron:

```text
3 años × 18 medidas = 54 comparaciones
```

Resultados:

| Año | Medidas verificadas | Coincidencias exactas | Diferencia máxima |
|---:|---:|---:|---:|
| 2024 | 18 | 18 | 0.00 |
| 2025 | 18 | 18 | 0.00 |
| 2026 | 18 | 18 | 0.00 |

Por tanto:

```text
Las 54 comparaciones monetarias coinciden exactamente.
```

La carga CSV → PostgreSQL no modificó ningún céntimo.

## 12. Configuración de conexión

La configuración pública está documentada en:

```text
.env.example
```

Las credenciales reales se almacenan en:

```text
.env
```

El archivo `.env` está excluido mediante `.gitignore`.

El helper:

```text
scripts/psql_project.sh
```

carga las variables del `.env` y ejecuta `psql` sin exponer la contraseña en los comandos.

Ejemplo:

```bash
bash scripts/psql_project.sh \
  -c "SELECT current_database(), current_user;"
```

## 13. Git Bash y pgAdmin

Se utilizan ambas herramientas.

### Git Bash y `psql`

Se emplean para:

- ejecutar scripts versionados;
- realizar cargas masivas;
- automatizar validaciones;
- reproducir la infraestructura;
- evitar procesos manuales.

### pgAdmin

Se utiliza para:

- explorar esquemas y tablas;
- revisar columnas e índices;
- ejecutar consultas visuales;
- inspeccionar los resultados;
- administrar el servidor local.

Los cambios estructurales deben quedar siempre reflejados en archivos SQL dentro del repositorio.

## 14. Scripts disponibles

| Script | Propósito |
|---|---|
| `001_create_schemas.sql` | Crear `staging` y `analytics` |
| `002_create_staging_table.sql` | Crear la tabla de 73 columnas |
| `003_load_staging.sql` | Cargar y validar los CSV |
| `004_validate_staging.sql` | Validar conteos, nulos y tamaño |
| `005_validate_amount_totals.sql` | Reconciliar los 54 totales exactos |

## 15. Pruebas automatizadas

Las pruebas verifican:

- estructura de 73 columnas;
- 18 medidas `NUMERIC(24,2)`;
- carga de los tres periodos;
- conteos esperados;
- creación del índice BRIN;
- reconciliación monetaria sin tolerancias;
- ausencia de credenciales reales en `.env.example`;
- conversión exacta de importes a centavos.

Resultado actual:

```text
54 passed
```

## 16. Estado final

La capa staging queda aprobada con:

- 7,698,240 registros cargados;
- 73 columnas;
- tres periodos validados;
- cero montos nulos;
- cero años inesperados;
- cero valores monetarios redondeados;
- 54 totales monetarios reconciliados exactamente;
- credenciales fuera de Git;
- scripts reproducibles;
- pruebas automatizadas aprobadas.

La siguiente etapa consiste en diseñar el modelo dimensional dentro del esquema `analytics`.