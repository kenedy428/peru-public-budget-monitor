\set ON_ERROR_STOP on
\timing on

BEGIN;

\echo 'Calculando totales monetarios de staging'

CREATE TEMP TABLE staging_amount_totals
ON COMMIT DROP
AS
SELECT
    ano_eje,

    SUM(monto_pia) AS monto_pia,
    SUM(monto_pim) AS monto_pim,
    SUM(monto_certificado_anual)
        AS monto_certificado_anual,
    SUM(monto_comprometido_anual)
        AS monto_comprometido_anual,

    SUM(monto_devengado_enero)
        AS monto_devengado_enero,
    SUM(monto_devengado_febrero)
        AS monto_devengado_febrero,
    SUM(monto_devengado_marzo)
        AS monto_devengado_marzo,
    SUM(monto_devengado_abril)
        AS monto_devengado_abril,
    SUM(monto_devengado_mayo)
        AS monto_devengado_mayo,
    SUM(monto_devengado_junio)
        AS monto_devengado_junio,
    SUM(monto_devengado_julio)
        AS monto_devengado_julio,
    SUM(monto_devengado_agosto)
        AS monto_devengado_agosto,
    SUM(monto_devengado_septiembre)
        AS monto_devengado_septiembre,
    SUM(monto_devengado_octubre)
        AS monto_devengado_octubre,
    SUM(monto_devengado_noviembre)
        AS monto_devengado_noviembre,
    SUM(monto_devengado_diciembre)
        AS monto_devengado_diciembre,

    SUM(monto_devengado_anual)
        AS monto_devengado_anual,
    SUM(monto_girado_anual)
        AS monto_girado_anual

FROM staging.mef_devengado
GROUP BY ano_eje;

\echo 'Calculando totales monetarios de analytics'

CREATE TEMP TABLE analytics_amount_totals
ON COMMIT DROP
AS
SELECT
    tiempo.ano_eje,

    SUM(fact.monto_pia) AS monto_pia,
    SUM(fact.monto_pim) AS monto_pim,
    SUM(fact.monto_certificado_anual)
        AS monto_certificado_anual,
    SUM(fact.monto_comprometido_anual)
        AS monto_comprometido_anual,

    SUM(fact.monto_devengado_enero)
        AS monto_devengado_enero,
    SUM(fact.monto_devengado_febrero)
        AS monto_devengado_febrero,
    SUM(fact.monto_devengado_marzo)
        AS monto_devengado_marzo,
    SUM(fact.monto_devengado_abril)
        AS monto_devengado_abril,
    SUM(fact.monto_devengado_mayo)
        AS monto_devengado_mayo,
    SUM(fact.monto_devengado_junio)
        AS monto_devengado_junio,
    SUM(fact.monto_devengado_julio)
        AS monto_devengado_julio,
    SUM(fact.monto_devengado_agosto)
        AS monto_devengado_agosto,
    SUM(fact.monto_devengado_septiembre)
        AS monto_devengado_septiembre,
    SUM(fact.monto_devengado_octubre)
        AS monto_devengado_octubre,
    SUM(fact.monto_devengado_noviembre)
        AS monto_devengado_noviembre,
    SUM(fact.monto_devengado_diciembre)
        AS monto_devengado_diciembre,

    SUM(fact.monto_devengado_anual)
        AS monto_devengado_anual,
    SUM(fact.monto_girado_anual)
        AS monto_girado_anual

FROM analytics.fact_ejecucion_presupuestal AS fact
JOIN analytics.dim_tiempo AS tiempo
    ON tiempo.tiempo_key = fact.tiempo_key
GROUP BY tiempo.ano_eje;

\echo 'Construyendo las 54 comparaciones exactas'

CREATE TEMP TABLE amount_reconciliation
ON COMMIT DROP
AS
SELECT
    COALESCE(
        staging.ano_eje,
        analytics.ano_eje
    ) AS ano_eje,

    measure.measure_name,
    measure.expected_total,
    measure.actual_total,

    (
        measure.actual_total
        - measure.expected_total
    ) AS difference,

    (
        measure.expected_total
        IS NOT DISTINCT FROM
        measure.actual_total
    ) AS matches_exactly

FROM staging_amount_totals AS staging

FULL JOIN analytics_amount_totals AS analytics
    USING (ano_eje)

CROSS JOIN LATERAL (
    VALUES
        (
            'monto_pia',
            staging.monto_pia,
            analytics.monto_pia
        ),
        (
            'monto_pim',
            staging.monto_pim,
            analytics.monto_pim
        ),
        (
            'monto_certificado_anual',
            staging.monto_certificado_anual,
            analytics.monto_certificado_anual
        ),
        (
            'monto_comprometido_anual',
            staging.monto_comprometido_anual,
            analytics.monto_comprometido_anual
        ),
        (
            'monto_devengado_enero',
            staging.monto_devengado_enero,
            analytics.monto_devengado_enero
        ),
        (
            'monto_devengado_febrero',
            staging.monto_devengado_febrero,
            analytics.monto_devengado_febrero
        ),
        (
            'monto_devengado_marzo',
            staging.monto_devengado_marzo,
            analytics.monto_devengado_marzo
        ),
        (
            'monto_devengado_abril',
            staging.monto_devengado_abril,
            analytics.monto_devengado_abril
        ),
        (
            'monto_devengado_mayo',
            staging.monto_devengado_mayo,
            analytics.monto_devengado_mayo
        ),
        (
            'monto_devengado_junio',
            staging.monto_devengado_junio,
            analytics.monto_devengado_junio
        ),
        (
            'monto_devengado_julio',
            staging.monto_devengado_julio,
            analytics.monto_devengado_julio
        ),
        (
            'monto_devengado_agosto',
            staging.monto_devengado_agosto,
            analytics.monto_devengado_agosto
        ),
        (
            'monto_devengado_septiembre',
            staging.monto_devengado_septiembre,
            analytics.monto_devengado_septiembre
        ),
        (
            'monto_devengado_octubre',
            staging.monto_devengado_octubre,
            analytics.monto_devengado_octubre
        ),
        (
            'monto_devengado_noviembre',
            staging.monto_devengado_noviembre,
            analytics.monto_devengado_noviembre
        ),
        (
            'monto_devengado_diciembre',
            staging.monto_devengado_diciembre,
            analytics.monto_devengado_diciembre
        ),
        (
            'monto_devengado_anual',
            staging.monto_devengado_anual,
            analytics.monto_devengado_anual
        ),
        (
            'monto_girado_anual',
            staging.monto_girado_anual,
            analytics.monto_girado_anual
        )
) AS measure (
    measure_name,
    expected_total,
    actual_total
);

\echo 'Diferencias monetarias encontradas'

SELECT
    ano_eje,
    measure_name,
    expected_total,
    actual_total,
    difference
FROM amount_reconciliation
WHERE NOT matches_exactly
ORDER BY
    ano_eje,
    measure_name;

\echo 'Resumen de reconciliación por año'

SELECT
    ano_eje,
    COUNT(*) AS measures_checked,
    COUNT(*) FILTER (
        WHERE matches_exactly
    ) AS exact_matches,
    COUNT(*) FILTER (
        WHERE NOT matches_exactly
    ) AS mismatches,
    COALESCE(
        MAX(ABS(difference)),
        0
    ) AS maximum_absolute_difference
FROM amount_reconciliation
GROUP BY ano_eje
ORDER BY ano_eje;

DO $$
DECLARE
    comparison_count INTEGER;
    year_count INTEGER;
    mismatch_count INTEGER;
BEGIN
    SELECT
        COUNT(*),
        COUNT(DISTINCT ano_eje),
        COUNT(*) FILTER (
            WHERE NOT matches_exactly
        )
    INTO
        comparison_count,
        year_count,
        mismatch_count
    FROM amount_reconciliation;

    IF comparison_count <> 54 THEN
        RAISE EXCEPTION
            'Se esperaban 54 comparaciones y se obtuvieron %.',
            comparison_count;
    END IF;

    IF year_count <> 3 THEN
        RAISE EXCEPTION
            'Se esperaban 3 años y se encontraron %.',
            year_count;
    END IF;

    IF mismatch_count <> 0 THEN
        RAISE EXCEPTION
            'Se encontraron % diferencias monetarias.',
            mismatch_count;
    END IF;

    RAISE NOTICE
        'Las 54 comparaciones monetarias coinciden exactamente.';
END;
$$;

COMMIT;

\echo 'Reconciliación monetaria de analytics completada correctamente.'