\set ON_ERROR_STOP on
\timing on

\echo 'Resumen físico de la tabla staging'

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

\echo 'Cardinalidad estimada y porcentaje de nulos'

WITH relation_statistics AS (
    SELECT
        relation.reltuples::BIGINT
            AS estimated_rows
    FROM pg_class AS relation
    JOIN pg_namespace AS namespace
        ON namespace.oid = relation.relnamespace
    WHERE namespace.nspname = 'staging'
      AND relation.relname = 'mef_devengado'
)
SELECT
    statistics.attname AS column_name,
    ROUND(
        statistics.null_frac::NUMERIC * 100,
        4
    ) AS null_percentage,
    CASE
        WHEN statistics.n_distinct < 0
        THEN ROUND(
            ABS(statistics.n_distinct)::NUMERIC
            * relation_statistics.estimated_rows
        )::BIGINT
        ELSE ROUND(
            statistics.n_distinct::NUMERIC
        )::BIGINT
    END AS estimated_distinct_values,
    statistics.avg_width AS average_width_bytes
FROM pg_stats AS statistics
CROSS JOIN relation_statistics
WHERE statistics.schemaname = 'staging'
  AND statistics.tablename = 'mef_devengado'
  AND statistics.attname NOT LIKE 'monto_%'
ORDER BY
    estimated_distinct_values DESC,
    statistics.attname;

\echo 'Columnas monetarias almacenadas en PostgreSQL'

SELECT
    column_name,
    data_type,
    numeric_precision,
    numeric_scale,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'staging'
  AND table_name = 'mef_devengado'
  AND column_name LIKE 'monto_%'
ORDER BY ordinal_position;