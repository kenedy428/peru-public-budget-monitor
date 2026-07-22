\set ON_ERROR_STOP on
\timing on

BEGIN;

-- Permite volver a ejecutar la carga desde cero.
DROP INDEX IF EXISTS staging.idx_mef_devengado_ano_eje_brin;

TRUNCATE TABLE staging.mef_devengado;

\echo 'Cargando datos consolidados de 2024...'

\copy staging.mef_devengado FROM 'data/processed/mef_devengado_2024_consolidated.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8', NULL '')

\echo 'Cargando datos consolidados de 2025...'

\copy staging.mef_devengado FROM 'data/processed/mef_devengado_2025_consolidated.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8', NULL '')

\echo 'Cargando datos consolidados de 2026...'

\copy staging.mef_devengado FROM 'data/processed/mef_devengado_2026_consolidated.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8', NULL '')

DO $$
DECLARE
    count_2024 BIGINT;
    count_2025 BIGINT;
    count_2026 BIGINT;
    count_total BIGINT;
BEGIN
    SELECT
        COUNT(*) FILTER (WHERE ano_eje = 2024),
        COUNT(*) FILTER (WHERE ano_eje = 2025),
        COUNT(*) FILTER (WHERE ano_eje = 2026),
        COUNT(*)
    INTO
        count_2024,
        count_2025,
        count_2026,
        count_total
    FROM staging.mef_devengado;

    IF count_2024 <> 2789605 THEN
        RAISE EXCEPTION
            'Conteo 2024 inesperado: %, esperado: 2789605',
            count_2024;
    END IF;

    IF count_2025 <> 2807021 THEN
        RAISE EXCEPTION
            'Conteo 2025 inesperado: %, esperado: 2807021',
            count_2025;
    END IF;

    IF count_2026 <> 2101614 THEN
        RAISE EXCEPTION
            'Conteo 2026 inesperado: %, esperado: 2101614',
            count_2026;
    END IF;

    IF count_total <> 7698240 THEN
        RAISE EXCEPTION
            'Conteo total inesperado: %, esperado: 7698240',
            count_total;
    END IF;
END
$$;

-- BRIN es un índice pequeño y apropiado porque los datos están
-- cargados en bloques ordenados por año.
CREATE INDEX idx_mef_devengado_ano_eje_brin
    ON staging.mef_devengado
    USING BRIN (ano_eje);

ANALYZE staging.mef_devengado;

COMMIT;

\echo 'Carga y validación completadas correctamente.'