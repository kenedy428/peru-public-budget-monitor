\set ON_ERROR_STOP on
\timing on

BEGIN;

CREATE TEMP TABLE expected_year_counts (
    ano_eje SMALLINT PRIMARY KEY,
    expected_rows BIGINT NOT NULL
) ON COMMIT DROP;

INSERT INTO expected_year_counts (
    ano_eje,
    expected_rows
)
VALUES
    (2024, 2789605),
    (2025, 2807021),
    (2026, 2101614);

\echo 'Validando cobertura de las ocho dimensiones'

CREATE TEMP TABLE dimension_coverage_by_year
ON COMMIT DROP
AS
SELECT
    staging.ano_eje,
    COUNT(*) AS staging_rows,

    COUNT(*) FILTER (
        WHERE tiempo.tiempo_key IS NULL
    ) AS missing_tiempo,

    COUNT(*) FILTER (
        WHERE institucion.institucion_key IS NULL
    ) AS missing_institucion,

    COUNT(*) FILTER (
        WHERE meta.meta_presupuestaria_key IS NULL
    ) AS missing_meta_presupuestaria,

    COUNT(*) FILTER (
        WHERE funcional.funcional_key IS NULL
    ) AS missing_funcional,

    COUNT(*) FILTER (
        WHERE financiamiento.financiamiento_key IS NULL
    ) AS missing_financiamiento,

    COUNT(*) FILTER (
        WHERE clasificador.clasificador_gasto_key IS NULL
    ) AS missing_clasificador_gasto,

    COUNT(*) FILTER (
        WHERE ubicacion.ubicacion_ejecutora_key IS NULL
    ) AS missing_ubicacion_ejecutora,

    COUNT(*) FILTER (
        WHERE departamento.departamento_meta_key IS NULL
    ) AS missing_departamento_meta

FROM staging.mef_devengado AS staging

LEFT JOIN analytics.dim_tiempo AS tiempo
    ON tiempo.ano_eje = staging.ano_eje

LEFT JOIN analytics.dim_institucion AS institucion
    ON institucion.ano_eje = staging.ano_eje
   AND institucion.sec_ejec = staging.sec_ejec

LEFT JOIN analytics.dim_meta_presupuestaria AS meta
    ON meta.ano_eje = staging.ano_eje
   AND meta.sec_ejec = staging.sec_ejec
   AND meta.sec_func = staging.sec_func
   AND meta.programa_ppto = staging.programa_ppto
   AND meta.tipo_act_proy = staging.tipo_act_proy
   AND meta.producto_proyecto = staging.producto_proyecto
   AND meta.actividad_accion_obra =
       staging.actividad_accion_obra
   AND meta.meta = staging.meta
   AND meta.finalidad = staging.finalidad

LEFT JOIN analytics.dim_funcional AS funcional
    ON funcional.funcion = staging.funcion
   AND funcional.division_funcional =
       staging.division_funcional
   AND funcional.grupo_funcional =
       staging.grupo_funcional

LEFT JOIN analytics.dim_financiamiento AS financiamiento
    ON financiamiento.fuente_financiamiento =
       staging.fuente_financiamiento
   AND financiamiento.rubro = staging.rubro
   AND financiamiento.tipo_recurso =
       staging.tipo_recurso

LEFT JOIN analytics.dim_clasificador_gasto AS clasificador
    ON clasificador.ano_eje = staging.ano_eje
   AND clasificador.categoria_gasto =
       staging.categoria_gasto
   AND clasificador.tipo_transaccion =
       staging.tipo_transaccion
   AND clasificador.generica = staging.generica
   AND clasificador.subgenerica = staging.subgenerica
   AND clasificador.subgenerica_det =
       staging.subgenerica_det
   AND clasificador.especifica = staging.especifica
   AND clasificador.especifica_det =
       staging.especifica_det

LEFT JOIN analytics.dim_ubicacion_ejecutora AS ubicacion
    ON ubicacion.departamento_ejecutora =
       staging.departamento_ejecutora
   AND ubicacion.provincia_ejecutora =
       staging.provincia_ejecutora
   AND ubicacion.distrito_ejecutora =
       staging.distrito_ejecutora

LEFT JOIN analytics.dim_departamento_meta AS departamento
    ON departamento.departamento_meta =
       staging.departamento_meta

GROUP BY staging.ano_eje;

\echo 'Cobertura dimensional por año'

SELECT
    ano_eje,
    staging_rows,
    missing_tiempo,
    missing_institucion,
    missing_meta_presupuestaria,
    missing_funcional,
    missing_financiamiento,
    missing_clasificador_gasto,
    missing_ubicacion_ejecutora,
    missing_departamento_meta,
    (
        missing_tiempo
        + missing_institucion
        + missing_meta_presupuestaria
        + missing_funcional
        + missing_financiamiento
        + missing_clasificador_gasto
        + missing_ubicacion_ejecutora
        + missing_departamento_meta
    ) AS total_missing_references
FROM dimension_coverage_by_year
ORDER BY ano_eje;

DO $$
DECLARE
    actual_total_rows BIGINT;
    missing_reference_count BIGINT;
    unexpected_year_count INTEGER;
BEGIN
    SELECT
        SUM(staging_rows)
    INTO actual_total_rows
    FROM dimension_coverage_by_year;

    SELECT
        SUM(
            missing_tiempo
            + missing_institucion
            + missing_meta_presupuestaria
            + missing_funcional
            + missing_financiamiento
            + missing_clasificador_gasto
            + missing_ubicacion_ejecutora
            + missing_departamento_meta
        )
    INTO missing_reference_count
    FROM dimension_coverage_by_year;

    SELECT COUNT(*)
    INTO unexpected_year_count
    FROM expected_year_counts AS expected
    FULL JOIN dimension_coverage_by_year AS actual
        USING (ano_eje)
    WHERE expected.expected_rows
        IS DISTINCT FROM actual.staging_rows;

    IF actual_total_rows <> 7698240 THEN
        RAISE EXCEPTION
            'Total inesperado. Esperado: 7698240, obtenido: %.',
            actual_total_rows;
    END IF;

    IF unexpected_year_count <> 0 THEN
        RAISE EXCEPTION
            'Los conteos por año no coinciden con staging.';
    END IF;

    IF missing_reference_count <> 0 THEN
        RAISE EXCEPTION
            'Se encontraron % referencias dimensionales ausentes.',
            missing_reference_count;
    END IF;

    RAISE NOTICE
        'Las 7,698,240 filas encuentran las ocho dimensiones.';
END;
$$;

COMMIT;

\echo 'Cobertura dimensional validada correctamente.'