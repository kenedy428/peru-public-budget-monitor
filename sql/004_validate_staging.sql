\set ON_ERROR_STOP on
\timing on

\echo 'Conteo de registros por año'

SELECT
    ano_eje,
    COUNT(*) AS row_count
FROM staging.mef_devengado
GROUP BY ano_eje
ORDER BY ano_eje;

\echo 'Resumen general'

SELECT
    COUNT(*) AS total_rows,
    MIN(ano_eje) AS minimum_year,
    MAX(ano_eje) AS maximum_year,
    COUNT(*) FILTER (
        WHERE ano_eje NOT IN (2024, 2025, 2026)
    ) AS unexpected_year_rows
FROM staging.mef_devengado;

\echo 'Validación de montos nulos'

SELECT
    COUNT(*) FILTER (
        WHERE monto_pia IS NULL
           OR monto_pim IS NULL
           OR monto_certificado_anual IS NULL
           OR monto_comprometido_anual IS NULL
           OR monto_devengado_enero IS NULL
           OR monto_devengado_febrero IS NULL
           OR monto_devengado_marzo IS NULL
           OR monto_devengado_abril IS NULL
           OR monto_devengado_mayo IS NULL
           OR monto_devengado_junio IS NULL
           OR monto_devengado_julio IS NULL
           OR monto_devengado_agosto IS NULL
           OR monto_devengado_septiembre IS NULL
           OR monto_devengado_octubre IS NULL
           OR monto_devengado_noviembre IS NULL
           OR monto_devengado_diciembre IS NULL
           OR monto_devengado_anual IS NULL
           OR monto_girado_anual IS NULL
    ) AS rows_with_null_amounts
FROM staging.mef_devengado;

\echo 'Tamaño físico de la tabla'

SELECT
    pg_size_pretty(
        pg_relation_size(
            'staging.mef_devengado'
        )
    ) AS table_size,
    pg_size_pretty(
        pg_indexes_size(
            'staging.mef_devengado'
        )
    ) AS indexes_size,
    pg_size_pretty(
        pg_total_relation_size(
            'staging.mef_devengado'
        )
    ) AS total_size;