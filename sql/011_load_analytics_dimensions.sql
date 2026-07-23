\set ON_ERROR_STOP on
\timing on

BEGIN;

-- Evita borrar dimensiones accidentalmente si la tabla de hechos
-- ya hubiera sido cargada.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM analytics.fact_ejecucion_presupuestal
    ) THEN
        RAISE EXCEPTION
            'La tabla de hechos contiene registros. '
            'No se recargarán las dimensiones.';
    END IF;
END;
$$;

TRUNCATE TABLE
    analytics.dim_tiempo,
    analytics.dim_institucion,
    analytics.dim_meta_presupuestaria,
    analytics.dim_funcional,
    analytics.dim_financiamiento,
    analytics.dim_clasificador_gasto,
    analytics.dim_ubicacion_ejecutora,
    analytics.dim_departamento_meta
RESTART IDENTITY;

\echo '1. Cargando dim_tiempo'

INSERT INTO analytics.dim_tiempo (
    ano_eje
)
SELECT DISTINCT
    ano_eje
FROM staging.mef_devengado
ORDER BY ano_eje;

\echo '2. Cargando dim_institucion'

INSERT INTO analytics.dim_institucion (
    ano_eje,
    sec_ejec,
    nivel_gobierno,
    nivel_gobierno_nombre,
    sector,
    sector_nombre,
    pliego,
    pliego_nombre,
    ejecutora,
    ejecutora_nombre
)
SELECT DISTINCT
    ano_eje,
    sec_ejec,
    nivel_gobierno,
    nivel_gobierno_nombre,
    sector,
    sector_nombre,
    pliego,
    pliego_nombre,
    ejecutora,
    ejecutora_nombre
FROM staging.mef_devengado
ORDER BY
    ano_eje,
    sec_ejec;

\echo '3. Cargando dim_meta_presupuestaria'

INSERT INTO analytics.dim_meta_presupuestaria (
    ano_eje,
    sec_ejec,
    sec_func,
    programa_ppto,
    programa_ppto_nombre,
    tipo_act_proy,
    producto_proyecto,
    producto_proyecto_nombre,
    actividad_accion_obra,
    actividad_accion_obra_nombre,
    meta,
    finalidad,
    meta_nombre
)
SELECT DISTINCT
    ano_eje,
    sec_ejec,
    sec_func,
    programa_ppto,
    programa_ppto_nombre,
    tipo_act_proy,
    producto_proyecto,
    producto_proyecto_nombre,
    actividad_accion_obra,
    actividad_accion_obra_nombre,
    meta,
    finalidad,
    meta_nombre
FROM staging.mef_devengado
ORDER BY
    ano_eje,
    sec_ejec,
    sec_func,
    programa_ppto,
    tipo_act_proy,
    producto_proyecto,
    actividad_accion_obra,
    meta,
    finalidad;

\echo '4. Cargando dim_funcional'

INSERT INTO analytics.dim_funcional (
    funcion,
    funcion_nombre,
    division_funcional,
    division_funcional_nombre,
    grupo_funcional,
    grupo_funcional_nombre
)
SELECT DISTINCT
    funcion,
    funcion_nombre,
    division_funcional,
    division_funcional_nombre,
    grupo_funcional,
    grupo_funcional_nombre
FROM staging.mef_devengado
ORDER BY
    funcion,
    division_funcional,
    grupo_funcional;

\echo '5. Cargando dim_financiamiento'

INSERT INTO analytics.dim_financiamiento (
    fuente_financiamiento,
    fuente_financiamiento_nombre,
    rubro,
    rubro_nombre,
    tipo_recurso,
    tipo_recurso_nombre
)
SELECT DISTINCT
    fuente_financiamiento,
    fuente_financiamiento_nombre,
    rubro,
    rubro_nombre,
    tipo_recurso,
    tipo_recurso_nombre
FROM staging.mef_devengado
ORDER BY
    fuente_financiamiento,
    rubro,
    tipo_recurso;

\echo '6. Cargando dim_clasificador_gasto'

INSERT INTO analytics.dim_clasificador_gasto (
    ano_eje,
    categoria_gasto,
    categoria_gasto_nombre,
    tipo_transaccion,
    tipo_transaccion_nombre,
    generica,
    generica_nombre,
    subgenerica,
    subgenerica_nombre,
    subgenerica_det,
    subgenerica_det_nombre,
    especifica,
    especifica_nombre,
    especifica_det,
    especifica_det_nombre
)
SELECT DISTINCT
    ano_eje,
    categoria_gasto,
    categoria_gasto_nombre,
    tipo_transaccion,
    tipo_transaccion_nombre,
    generica,
    generica_nombre,
    subgenerica,
    subgenerica_nombre,
    subgenerica_det,
    subgenerica_det_nombre,
    especifica,
    especifica_nombre,
    especifica_det,
    especifica_det_nombre
FROM staging.mef_devengado
ORDER BY
    ano_eje,
    categoria_gasto,
    tipo_transaccion,
    generica,
    subgenerica,
    subgenerica_det,
    especifica,
    especifica_det;

\echo '7. Cargando dim_ubicacion_ejecutora'

INSERT INTO analytics.dim_ubicacion_ejecutora (
    departamento_ejecutora,
    departamento_ejecutora_nombre,
    provincia_ejecutora,
    provincia_ejecutora_nombre,
    distrito_ejecutora,
    distrito_ejecutora_nombre
)
SELECT DISTINCT
    departamento_ejecutora,
    departamento_ejecutora_nombre,
    provincia_ejecutora,
    provincia_ejecutora_nombre,
    distrito_ejecutora,
    distrito_ejecutora_nombre
FROM staging.mef_devengado
ORDER BY
    departamento_ejecutora,
    provincia_ejecutora,
    distrito_ejecutora;

\echo '8. Cargando dim_departamento_meta'

INSERT INTO analytics.dim_departamento_meta (
    departamento_meta,
    departamento_meta_nombre
)
SELECT DISTINCT
    departamento_meta,
    departamento_meta_nombre
FROM staging.mef_devengado
ORDER BY departamento_meta;

ANALYZE analytics.dim_tiempo;
ANALYZE analytics.dim_institucion;
ANALYZE analytics.dim_meta_presupuestaria;
ANALYZE analytics.dim_funcional;
ANALYZE analytics.dim_financiamiento;
ANALYZE analytics.dim_clasificador_gasto;
ANALYZE analytics.dim_ubicacion_ejecutora;
ANALYZE analytics.dim_departamento_meta;

CREATE TEMP TABLE expected_dimension_counts (
    table_name TEXT PRIMARY KEY,
    expected_count BIGINT NOT NULL
) ON COMMIT DROP;

INSERT INTO expected_dimension_counts (
    table_name,
    expected_count
)
VALUES
    ('dim_tiempo', 3),
    ('dim_institucion', 8602),
    ('dim_meta_presupuestaria', 790865),
    ('dim_funcional', 387),
    ('dim_financiamiento', 175),
    ('dim_clasificador_gasto', 1602),
    ('dim_ubicacion_ejecutora', 1892),
    ('dim_departamento_meta', 27);

\echo 'Conteos de dimensiones cargadas'

SELECT
    'dim_tiempo' AS table_name,
    COUNT(*) AS actual_count
FROM analytics.dim_tiempo

UNION ALL

SELECT
    'dim_institucion',
    COUNT(*)
FROM analytics.dim_institucion

UNION ALL

SELECT
    'dim_meta_presupuestaria',
    COUNT(*)
FROM analytics.dim_meta_presupuestaria

UNION ALL

SELECT
    'dim_funcional',
    COUNT(*)
FROM analytics.dim_funcional

UNION ALL

SELECT
    'dim_financiamiento',
    COUNT(*)
FROM analytics.dim_financiamiento

UNION ALL

SELECT
    'dim_clasificador_gasto',
    COUNT(*)
FROM analytics.dim_clasificador_gasto

UNION ALL

SELECT
    'dim_ubicacion_ejecutora',
    COUNT(*)
FROM analytics.dim_ubicacion_ejecutora

UNION ALL

SELECT
    'dim_departamento_meta',
    COUNT(*)
FROM analytics.dim_departamento_meta

ORDER BY table_name;

DO $$
DECLARE
    dimension_record RECORD;
    actual_count BIGINT;
BEGIN
    FOR dimension_record IN
        SELECT
            table_name,
            expected_count
        FROM expected_dimension_counts
        ORDER BY table_name
    LOOP
        EXECUTE FORMAT(
            'SELECT COUNT(*) FROM analytics.%I',
            dimension_record.table_name
        )
        INTO actual_count;

        IF actual_count <> dimension_record.expected_count THEN
            RAISE EXCEPTION
                'Conteo incorrecto para %. Esperado: %, obtenido: %.',
                dimension_record.table_name,
                dimension_record.expected_count,
                actual_count;
        END IF;
    END LOOP;

    RAISE NOTICE
        'Las ocho dimensiones coinciden con los conteos esperados.';
END;
$$;

COMMIT;

\echo 'Carga de dimensiones completada correctamente.'