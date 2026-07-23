\set ON_ERROR_STOP on
\timing on

\echo 'Creando conjuntos semánticos candidatos'

CREATE TEMP TABLE candidate_institution AS
SELECT DISTINCT
    ano_eje,
    nivel_gobierno,
    nivel_gobierno_nombre,
    sector,
    sector_nombre,
    pliego,
    pliego_nombre,
    sec_ejec,
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

CREATE TEMP TABLE candidate_functional AS
SELECT DISTINCT
    funcion,
    funcion_nombre,
    division_funcional,
    division_funcional_nombre,
    grupo_funcional,
    grupo_funcional_nombre
FROM staging.mef_devengado;

CREATE TEMP TABLE candidate_executor_geography AS
SELECT DISTINCT
    departamento_ejecutora,
    departamento_ejecutora_nombre,
    provincia_ejecutora,
    provincia_ejecutora_nombre,
    distrito_ejecutora,
    distrito_ejecutora_nombre
FROM staging.mef_devengado;

CREATE TEMP TABLE candidate_meta_geography AS
SELECT DISTINCT
    departamento_meta,
    departamento_meta_nombre
FROM staging.mef_devengado;

CREATE TEMP TABLE candidate_financing AS
SELECT DISTINCT
    fuente_financiamiento,
    fuente_financiamiento_nombre,
    rubro,
    rubro_nombre,
    tipo_recurso,
    tipo_recurso_nombre
FROM staging.mef_devengado;

CREATE TEMP TABLE candidate_expense_classifier AS
SELECT DISTINCT
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

\echo 'Resumen exacto de relaciones candidatas'

WITH relationship_checks AS (
    SELECT
        'institucion: año + SEC_EJEC'::TEXT
            AS relationship_name,
        (
            SELECT COUNT(*)
            FROM (
                SELECT ano_eje, sec_ejec
                FROM candidate_institution
                GROUP BY ano_eje, sec_ejec
            ) AS keys
        )::BIGINT AS natural_key_count,
        (
            SELECT COUNT(*)
            FROM candidate_institution
        )::BIGINT AS attribute_variant_count,
        (
            SELECT COUNT(*)
            FROM (
                SELECT ano_eje, sec_ejec
                FROM candidate_institution
                GROUP BY ano_eje, sec_ejec
                HAVING COUNT(*) > 1
            ) AS conflicts
        )::BIGINT AS conflicting_key_count

    UNION ALL

    SELECT
        'institucion: año + EJECUTORA',
        (
            SELECT COUNT(*)
            FROM (
                SELECT ano_eje, ejecutora
                FROM candidate_institution
                GROUP BY ano_eje, ejecutora
            ) AS keys
        ),
        (
            SELECT COUNT(*)
            FROM candidate_institution
        ),
        (
            SELECT COUNT(*)
            FROM (
                SELECT ano_eje, ejecutora
                FROM candidate_institution
                GROUP BY ano_eje, ejecutora
                HAVING COUNT(*) > 1
            ) AS conflicts
        )

    UNION ALL

    SELECT
        'meta: año + SEC_EJEC + SEC_FUNC',
        (
            SELECT COUNT(*)
            FROM (
                SELECT ano_eje, sec_ejec, sec_func
                FROM candidate_programmatic_meta
                GROUP BY ano_eje, sec_ejec, sec_func
            ) AS keys
        ),
        (
            SELECT COUNT(*)
            FROM candidate_programmatic_meta
        ),
        (
            SELECT COUNT(*)
            FROM (
                SELECT ano_eje, sec_ejec, sec_func
                FROM candidate_programmatic_meta
                GROUP BY ano_eje, sec_ejec, sec_func
                HAVING COUNT(*) > 1
            ) AS conflicts
        )

    UNION ALL

    SELECT
        'meta: año + SEC_EJEC + META',
        (
            SELECT COUNT(*)
            FROM (
                SELECT ano_eje, sec_ejec, meta
                FROM candidate_programmatic_meta
                GROUP BY ano_eje, sec_ejec, meta
            ) AS keys
        ),
        (
            SELECT COUNT(*)
            FROM candidate_programmatic_meta
        ),
        (
            SELECT COUNT(*)
            FROM (
                SELECT ano_eje, sec_ejec, meta
                FROM candidate_programmatic_meta
                GROUP BY ano_eje, sec_ejec, meta
                HAVING COUNT(*) > 1
            ) AS conflicts
        )

    UNION ALL

    SELECT
        'función + división + grupo',
        (
            SELECT COUNT(*)
            FROM (
                SELECT
                    funcion,
                    division_funcional,
                    grupo_funcional
                FROM candidate_functional
                GROUP BY
                    funcion,
                    division_funcional,
                    grupo_funcional
            ) AS keys
        ),
        (
            SELECT COUNT(*)
            FROM candidate_functional
        ),
        (
            SELECT COUNT(*)
            FROM (
                SELECT
                    funcion,
                    division_funcional,
                    grupo_funcional
                FROM candidate_functional
                GROUP BY
                    funcion,
                    division_funcional,
                    grupo_funcional
                HAVING COUNT(*) > 1
            ) AS conflicts
        )

    UNION ALL

    SELECT
        'ubigeo de ejecutora',
        (
            SELECT COUNT(*)
            FROM (
                SELECT
                    departamento_ejecutora,
                    provincia_ejecutora,
                    distrito_ejecutora
                FROM candidate_executor_geography
                GROUP BY
                    departamento_ejecutora,
                    provincia_ejecutora,
                    distrito_ejecutora
            ) AS keys
        ),
        (
            SELECT COUNT(*)
            FROM candidate_executor_geography
        ),
        (
            SELECT COUNT(*)
            FROM (
                SELECT
                    departamento_ejecutora,
                    provincia_ejecutora,
                    distrito_ejecutora
                FROM candidate_executor_geography
                GROUP BY
                    departamento_ejecutora,
                    provincia_ejecutora,
                    distrito_ejecutora
                HAVING COUNT(*) > 1
            ) AS conflicts
        )

    UNION ALL

    SELECT
        'departamento de meta',
        (
            SELECT COUNT(*)
            FROM (
                SELECT departamento_meta
                FROM candidate_meta_geography
                GROUP BY departamento_meta
            ) AS keys
        ),
        (
            SELECT COUNT(*)
            FROM candidate_meta_geography
        ),
        (
            SELECT COUNT(*)
            FROM (
                SELECT departamento_meta
                FROM candidate_meta_geography
                GROUP BY departamento_meta
                HAVING COUNT(*) > 1
            ) AS conflicts
        )

    UNION ALL

    SELECT
        'fuente + rubro + tipo de recurso',
        (
            SELECT COUNT(*)
            FROM (
                SELECT
                    fuente_financiamiento,
                    rubro,
                    tipo_recurso
                FROM candidate_financing
                GROUP BY
                    fuente_financiamiento,
                    rubro,
                    tipo_recurso
            ) AS keys
        ),
        (
            SELECT COUNT(*)
            FROM candidate_financing
        ),
        (
            SELECT COUNT(*)
            FROM (
                SELECT
                    fuente_financiamiento,
                    rubro,
                    tipo_recurso
                FROM candidate_financing
                GROUP BY
                    fuente_financiamiento,
                    rubro,
                    tipo_recurso
                HAVING COUNT(*) > 1
            ) AS conflicts
        )

    UNION ALL

    SELECT
        'clasificador completo de gasto',
        (
            SELECT COUNT(*)
            FROM (
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
            ) AS keys
        ),
        (
            SELECT COUNT(*)
            FROM candidate_expense_classifier
        ),
        (
            SELECT COUNT(*)
            FROM (
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
                HAVING COUNT(*) > 1
            ) AS conflicts
        )
)
SELECT
    relationship_name,
    natural_key_count,
    attribute_variant_count,
    conflicting_key_count,
    (
        attribute_variant_count
        - natural_key_count
    ) AS additional_attribute_variants
FROM relationship_checks
ORDER BY relationship_name;