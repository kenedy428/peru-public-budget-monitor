\set ON_ERROR_STOP on
\timing on

\echo 'Preparando candidatos dimensionales refinados'

CREATE TEMP TABLE candidate_institution AS
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
FROM staging.mef_devengado;

CREATE TEMP TABLE candidate_programmatic_meta AS
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
FROM staging.mef_devengado;

CREATE TEMP TABLE candidate_expense_classifier AS
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
FROM staging.mef_devengado;

ANALYZE candidate_institution;
ANALYZE candidate_programmatic_meta;
ANALYZE candidate_expense_classifier;

\echo '1. Refinamiento de la clave programática'

WITH key_with_finality AS (
    SELECT
        ano_eje,
        sec_ejec,
        sec_func,
        finalidad,
        COUNT(*) AS attribute_variants
    FROM candidate_programmatic_meta
    GROUP BY
        ano_eje,
        sec_ejec,
        sec_func,
        finalidad
),
full_programmatic_key AS (
    SELECT
        ano_eje,
        sec_ejec,
        sec_func,
        programa_ppto,
        tipo_act_proy,
        producto_proyecto,
        actividad_accion_obra,
        meta,
        finalidad,
        COUNT(*) AS attribute_variants
    FROM candidate_programmatic_meta
    GROUP BY
        ano_eje,
        sec_ejec,
        sec_func,
        programa_ppto,
        tipo_act_proy,
        producto_proyecto,
        actividad_accion_obra,
        meta,
        finalidad
)
SELECT
    'año + entidad + sec_func + finalidad'
        AS candidate_key,
    COUNT(*) AS key_count,
    COUNT(*) FILTER (
        WHERE attribute_variants > 1
    ) AS conflicting_keys,
    COALESCE(
        MAX(attribute_variants),
        0
    ) AS maximum_variants
FROM key_with_finality

UNION ALL

SELECT
    'cadena programática completa',
    COUNT(*),
    COUNT(*) FILTER (
        WHERE attribute_variants > 1
    ),
    COALESCE(
        MAX(attribute_variants),
        0
    )
FROM full_programmatic_key;

\echo '2. Cambios institucionales entre años'

WITH institutional_history AS (
    SELECT
        sec_ejec,
        COUNT(DISTINCT ano_eje)
            AS years_present,
        COUNT(
            DISTINCT ROW(
                nivel_gobierno,
                nivel_gobierno_nombre,
                sector,
                sector_nombre,
                pliego,
                pliego_nombre,
                ejecutora,
                ejecutora_nombre
            )
        ) AS attribute_versions
    FROM candidate_institution
    GROUP BY sec_ejec
)
SELECT
    COUNT(*) AS distinct_entities,
    COUNT(*) FILTER (
        WHERE attribute_versions > 1
    ) AS entities_with_historical_changes,
    MAX(attribute_versions)
        AS maximum_attribute_versions
FROM institutional_history;

\echo '3. Cambios reales del clasificador entre años'

WITH classifier_history AS (
    SELECT
        categoria_gasto,
        tipo_transaccion,
        generica,
        subgenerica,
        subgenerica_det,
        especifica,
        especifica_det,
        COUNT(DISTINCT ano_eje)
            AS years_present,
        COUNT(
            DISTINCT ROW(
                categoria_gasto_nombre,
                tipo_transaccion_nombre,
                generica_nombre,
                subgenerica_nombre,
                subgenerica_det_nombre,
                especifica_nombre,
                especifica_det_nombre
            )
        ) AS description_versions
    FROM candidate_expense_classifier
    GROUP BY
        categoria_gasto,
        tipo_transaccion,
        generica,
        subgenerica,
        subgenerica_det,
        especifica,
        especifica_det
),
within_year_conflicts AS (
    SELECT
        ano_eje,
        categoria_gasto,
        tipo_transaccion,
        generica,
        subgenerica,
        subgenerica_det,
        especifica,
        especifica_det
    FROM candidate_expense_classifier
    GROUP BY
        ano_eje,
        categoria_gasto,
        tipo_transaccion,
        generica,
        subgenerica,
        subgenerica_det,
        especifica,
        especifica_det
    HAVING COUNT(
        DISTINCT ROW(
            categoria_gasto_nombre,
            tipo_transaccion_nombre,
            generica_nombre,
            subgenerica_nombre,
            subgenerica_det_nombre,
            especifica_nombre,
            especifica_det_nombre
        )
    ) > 1
)
SELECT
    COUNT(*) AS classifier_code_chains,
    COUNT(*) FILTER (
        WHERE description_versions > 1
    ) AS actual_cross_year_description_changes,
    (
        SELECT COUNT(*)
        FROM within_year_conflicts
    ) AS within_year_conflicts,
    MAX(description_versions)
        AS maximum_description_versions
FROM classifier_history;

\echo 'Detalle de los cambios reales del clasificador'

WITH changed_classifier_keys AS (
    SELECT
        categoria_gasto,
        tipo_transaccion,
        generica,
        subgenerica,
        subgenerica_det,
        especifica,
        especifica_det
    FROM candidate_expense_classifier
    GROUP BY
        categoria_gasto,
        tipo_transaccion,
        generica,
        subgenerica,
        subgenerica_det,
        especifica,
        especifica_det
    HAVING COUNT(
        DISTINCT ROW(
            categoria_gasto_nombre,
            tipo_transaccion_nombre,
            generica_nombre,
            subgenerica_nombre,
            subgenerica_det_nombre,
            especifica_nombre,
            especifica_det_nombre
        )
    ) > 1
)
SELECT
    classifier.ano_eje,
    classifier.categoria_gasto,
    classifier.tipo_transaccion,
    classifier.generica,
    classifier.subgenerica,
    classifier.subgenerica_det,
    classifier.especifica,
    classifier.especifica_det,
    classifier.subgenerica_nombre,
    classifier.especifica_nombre,
    classifier.especifica_det_nombre
FROM candidate_expense_classifier AS classifier
JOIN changed_classifier_keys AS changed
    USING (
        categoria_gasto,
        tipo_transaccion,
        generica,
        subgenerica,
        subgenerica_det,
        especifica,
        especifica_det
    )
ORDER BY
    classifier.categoria_gasto,
    classifier.generica,
    classifier.subgenerica,
    classifier.subgenerica_det,
    classifier.especifica,
    classifier.especifica_det,
    classifier.ano_eje;