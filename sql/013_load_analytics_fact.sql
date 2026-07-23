\set ON_ERROR_STOP on
\timing on

BEGIN;

-- ============================================================
-- Validación previa de las dimensiones
-- ============================================================

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

        IF actual_count
            <> dimension_record.expected_count
        THEN
            RAISE EXCEPTION
                'Conteo incorrecto en %. Esperado: %, obtenido: %.',
                dimension_record.table_name,
                dimension_record.expected_count,
                actual_count;
        END IF;
    END LOOP;

    RAISE NOTICE
        'Las ocho dimensiones están disponibles con los conteos esperados.';
END;
$$;

-- ============================================================
-- Recarga de la tabla de hechos
-- ============================================================

TRUNCATE TABLE
    analytics.fact_ejecucion_presupuestal;

\echo 'Cargando fact_ejecucion_presupuestal'

INSERT INTO analytics.fact_ejecucion_presupuestal (
    tiempo_key,
    institucion_key,
    meta_presupuestaria_key,
    funcional_key,
    financiamiento_key,
    clasificador_gasto_key,
    ubicacion_ejecutora_key,
    departamento_meta_key,

    monto_pia,
    monto_pim,
    monto_certificado_anual,
    monto_comprometido_anual,

    monto_devengado_enero,
    monto_devengado_febrero,
    monto_devengado_marzo,
    monto_devengado_abril,
    monto_devengado_mayo,
    monto_devengado_junio,
    monto_devengado_julio,
    monto_devengado_agosto,
    monto_devengado_septiembre,
    monto_devengado_octubre,
    monto_devengado_noviembre,
    monto_devengado_diciembre,

    monto_devengado_anual,
    monto_girado_anual
)
SELECT
    tiempo.tiempo_key,
    institucion.institucion_key,
    meta.meta_presupuestaria_key,
    funcional.funcional_key,
    financiamiento.financiamiento_key,
    clasificador.clasificador_gasto_key,
    ubicacion.ubicacion_ejecutora_key,
    departamento.departamento_meta_key,

    staging.monto_pia,
    staging.monto_pim,
    staging.monto_certificado_anual,
    staging.monto_comprometido_anual,

    staging.monto_devengado_enero,
    staging.monto_devengado_febrero,
    staging.monto_devengado_marzo,
    staging.monto_devengado_abril,
    staging.monto_devengado_mayo,
    staging.monto_devengado_junio,
    staging.monto_devengado_julio,
    staging.monto_devengado_agosto,
    staging.monto_devengado_septiembre,
    staging.monto_devengado_octubre,
    staging.monto_devengado_noviembre,
    staging.monto_devengado_diciembre,

    staging.monto_devengado_anual,
    staging.monto_girado_anual

FROM staging.mef_devengado AS staging

JOIN analytics.dim_tiempo AS tiempo
    ON tiempo.ano_eje = staging.ano_eje

JOIN analytics.dim_institucion AS institucion
    ON institucion.ano_eje = staging.ano_eje
   AND institucion.sec_ejec = staging.sec_ejec

JOIN analytics.dim_meta_presupuestaria AS meta
    ON meta.ano_eje = staging.ano_eje
   AND meta.sec_ejec = staging.sec_ejec
   AND meta.sec_func = staging.sec_func
   AND meta.programa_ppto =
       staging.programa_ppto
   AND meta.tipo_act_proy =
       staging.tipo_act_proy
   AND meta.producto_proyecto =
       staging.producto_proyecto
   AND meta.actividad_accion_obra =
       staging.actividad_accion_obra
   AND meta.meta = staging.meta
   AND meta.finalidad = staging.finalidad

JOIN analytics.dim_funcional AS funcional
    ON funcional.funcion = staging.funcion
   AND funcional.division_funcional =
       staging.division_funcional
   AND funcional.grupo_funcional =
       staging.grupo_funcional

JOIN analytics.dim_financiamiento
    AS financiamiento
    ON financiamiento.fuente_financiamiento =
       staging.fuente_financiamiento
   AND financiamiento.rubro = staging.rubro
   AND financiamiento.tipo_recurso =
       staging.tipo_recurso

JOIN analytics.dim_clasificador_gasto
    AS clasificador
    ON clasificador.ano_eje = staging.ano_eje
   AND clasificador.categoria_gasto =
       staging.categoria_gasto
   AND clasificador.tipo_transaccion =
       staging.tipo_transaccion
   AND clasificador.generica =
       staging.generica
   AND clasificador.subgenerica =
       staging.subgenerica
   AND clasificador.subgenerica_det =
       staging.subgenerica_det
   AND clasificador.especifica =
       staging.especifica
   AND clasificador.especifica_det =
       staging.especifica_det

JOIN analytics.dim_ubicacion_ejecutora
    AS ubicacion
    ON ubicacion.departamento_ejecutora =
       staging.departamento_ejecutora
   AND ubicacion.provincia_ejecutora =
       staging.provincia_ejecutora
   AND ubicacion.distrito_ejecutora =
       staging.distrito_ejecutora

JOIN analytics.dim_departamento_meta
    AS departamento
    ON departamento.departamento_meta =
       staging.departamento_meta;

-- ============================================================
-- Validación de conteos
-- ============================================================

CREATE TEMP TABLE fact_counts_by_year
ON COMMIT DROP
AS
SELECT
    tiempo.ano_eje,
    COUNT(*) AS row_count
FROM analytics.fact_ejecucion_presupuestal
    AS fact
JOIN analytics.dim_tiempo AS tiempo
    ON tiempo.tiempo_key = fact.tiempo_key
GROUP BY tiempo.ano_eje;

\echo 'Conteos de la tabla de hechos por año'

SELECT
    ano_eje,
    row_count
FROM fact_counts_by_year
ORDER BY ano_eje;

DO $$
DECLARE
    total_rows BIGINT;
    mismatched_years INTEGER;
BEGIN
    SELECT
        COALESCE(
            SUM(row_count),
            0
        )
    INTO total_rows
    FROM fact_counts_by_year;

    SELECT COUNT(*)
    INTO mismatched_years
    FROM (
        VALUES
            (2024::SMALLINT, 2789605::BIGINT),
            (2025::SMALLINT, 2807021::BIGINT),
            (2026::SMALLINT, 2101614::BIGINT)
    ) AS expected (
        ano_eje,
        expected_rows
    )
    FULL JOIN fact_counts_by_year AS actual
        USING (ano_eje)
    WHERE expected.expected_rows
        IS DISTINCT FROM actual.row_count;

    IF total_rows <> 7698240 THEN
        RAISE EXCEPTION
            'Conteo total incorrecto. Esperado: 7698240, obtenido: %.',
            total_rows;
    END IF;

    IF mismatched_years <> 0 THEN
        RAISE EXCEPTION
            'Uno o más conteos anuales no coinciden.';
    END IF;

    RAISE NOTICE
        'La tabla de hechos contiene exactamente 7,698,240 filas.';
END;
$$;

ANALYZE
    analytics.fact_ejecucion_presupuestal;

COMMIT;

\echo 'Carga de la tabla de hechos completada correctamente.'