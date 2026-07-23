# Diseño del modelo dimensional de ejecución presupuestal

## 1. Objetivo

Diseñar un modelo estrella en el esquema `analytics` a partir de los datos validados de `staging.mef_devengado`, orientado a consultas analíticas y consumo desde Power BI.

## 2. Evidencia utilizada

El diseño se basa en:

- el diccionario oficial de 73 variables del MEF;
- el perfil de cardinalidades de PostgreSQL;
- validaciones exactas de claves naturales;
- análisis de conflictos de códigos y descripciones;
- los 7,698,240 registros consolidados de 2024, 2025 y 2026.

Las decisiones no se basan únicamente en los nombres de las columnas.

## 3. Grano de la tabla de hechos

Una fila de `fact_ejecucion_presupuestal` representa una combinación única de:

- año de ejecución;
- institución;
- meta presupuestaria;
- clasificación funcional;
- financiamiento;
- clasificador de gasto;
- ubicación geográfica de la ejecutora;
- departamento de ejecución de la meta.

La tabla de hechos conservará las 7,698,240 filas de staging y las 18 medidas monetarias.

## 4. Dimensiones

### 4.1 `dim_tiempo`

Contiene el año de ejecución presupuestal.

Clave natural:

```text
ANO_EJE
```

Filas esperadas: 3.

### 4.2 `dim_institucion`

Contiene nivel de gobierno, sector, pliego y unidad ejecutora.

Clave natural:

```text
ANO_EJE + SEC_EJEC
```

`EJECUTORA` no se utiliza como identificador porque el mismo código se reutiliza para distintas entidades.

Se identificaron 2,889 entidades y 8 entidades con cambios de atributos entre años. Se conservará una versión anual.

Filas esperadas: 8,602.

### 4.3 `dim_meta_presupuestaria`

Contiene la cadena programática y la finalidad asociada a la meta.

Clave natural:

```text
ANO_EJE
+ SEC_EJEC
+ SEC_FUNC
+ PROGRAMA_PPTO
+ TIPO_ACT_PROY
+ PRODUCTO_PROYECTO
+ ACTIVIDAD_ACCION_OBRA
+ META
+ FINALIDAD
```

La cadena completa produjo 790,865 claves y cero conflictos.

Las claves reducidas basadas solo en `SEC_FUNC`, `META` o `FINALIDAD` fueron rechazadas porque mezclaban metas diferentes.

Filas esperadas: 790,865.

### 4.4 `dim_funcional`

Contiene:

```text
FUNCION
DIVISION_FUNCIONAL
GRUPO_FUNCIONAL
```

La combinación completa produjo 387 filas y cero conflictos.

### 4.5 `dim_financiamiento`

Contiene:

```text
FUENTE_FINANCIAMIENTO
RUBRO
TIPO_RECURSO
```

La combinación completa produjo 175 filas y cero conflictos.

### 4.6 `dim_clasificador_gasto`

Contiene la cadena completa del clasificador presupuestario.

Clave natural:

```text
ANO_EJE
+ CATEGORIA_GASTO
+ TIPO_TRANSACCION
+ GENERICA
+ SUBGENERICA
+ SUBGENERICA_DET
+ ESPECIFICA
+ ESPECIFICA_DET
```

Se identificaron 553 cadenas de códigos.

Cinco cadenas presentan cambios reales de descripción entre años y no existen conflictos dentro del mismo año. Se conservará una versión anual.

Filas esperadas: 1,602.

### 4.7 `dim_ubicacion_ejecutora`

Contiene departamento, provincia y distrito donde se ubica la entidad.

La combinación jerárquica completa produjo 1,892 filas y cero conflictos.

### 4.8 `dim_departamento_meta`

Contiene el departamento donde se ejecuta la meta presupuestaria.

Produjo 27 filas y cero conflictos.

## 5. Tabla de hechos

La tabla:

```text
analytics.fact_ejecucion_presupuestal
```

contendrá:

- claves sustitutas hacia las dimensiones;
- las 18 medidas monetarias;
- 7,698,240 registros.

Las medidas permanecerán como:

```sql
NUMERIC(24, 2)
```

## 6. Estrategia histórica

Para las dimensiones institucional y de clasificador de gasto se utilizará una versión anual de los atributos.

Esta estrategia evita sobrescribir nombres o clasificaciones históricas y es más sencilla que implementar un SCD tipo 2 basado en fechas para una fuente anual.

## 7. Validaciones requeridas

Después de cargar el modelo deberán cumplirse:

- 7,698,240 filas en la tabla de hechos;
- cero claves foráneas nulas;
- cero registros huérfanos;
- coincidencia exacta de las 18 medidas por cada año;
- 54 de 54 totales monetarios reconciliados;
- diferencia monetaria máxima de S/ 0.00.

## 8. Uso en Power BI

Power BI se conectará al esquema `analytics`, no directamente a `staging`.

El modelo estrella permitirá:

- relaciones de uno a muchos;
- filtros por dimensiones;
- mejor compresión;
- medidas DAX más simples;
- menor ambigüedad en las relaciones;
- navegación por jerarquías presupuestales.