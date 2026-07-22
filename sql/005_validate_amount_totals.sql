\set ON_ERROR_STOP on
\timing on

-- Los valores esperados proceden de una auditoría exacta
-- realizada con centavos enteros, sin utilizar float.

BEGIN;

CREATE TEMP TABLE expected_amount_totals (
    ano_eje SMALLINT PRIMARY KEY,
    monto_pia NUMERIC(38, 2) NOT NULL,
    monto_pim NUMERIC(38, 2) NOT NULL,
    monto_certificado_anual NUMERIC(38, 2) NOT NULL,
    monto_comprometido_anual NUMERIC(38, 2) NOT NULL,
    monto_devengado_enero NUMERIC(38, 2) NOT NULL,
    monto_devengado_febrero NUMERIC(38, 2) NOT NULL,
    monto_devengado_marzo NUMERIC(38, 2) NOT NULL,
    monto_devengado_abril NUMERIC(38, 2) NOT NULL,
    monto_devengado_mayo NUMERIC(38, 2) NOT NULL,
    monto_devengado_junio NUMERIC(38, 2) NOT NULL,
    monto_devengado_julio NUMERIC(38, 2) NOT NULL,
    monto_devengado_agosto NUMERIC(38, 2) NOT NULL,
    monto_devengado_septiembre NUMERIC(38, 2) NOT NULL,
    monto_devengado_octubre NUMERIC(38, 2) NOT NULL,
    monto_devengado_noviembre NUMERIC(38, 2) NOT NULL,
    monto_devengado_diciembre NUMERIC(38, 2) NOT NULL,
    monto_devengado_anual NUMERIC(38, 2) NOT NULL,
    monto_girado_anual NUMERIC(38, 2) NOT NULL
);

INSERT INTO expected_amount_totals (
    ano_eje,
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
VALUES
    (2024, 240806216645.00, 262058019205.00, 251195736886.79, 244031793912.28, 13020429766.62, 22366088144.25, 16129703014.05, 18108483521.96, 17920910133.30, 17563158158.52, 19655249719.81, 22555669613.26, 17896216359.46, 20920327111.85, 19239284024.66, 33521182469.75, 238896702037.49, 238546847706.99),
    (2025, 251801045185.00, 272450859407.00, 263085709247.47, 258771064633.88, 16835113842.62, 21907083519.65, 17848446335.70, 17323461642.53, 19059256742.81, 20553648217.10, 21464948310.86, 23718101029.81, 21162887768.59, 19635180470.43, 19692526467.13, 34479610194.91, 253680264542.14, 253416984330.22),
    (2026, 257561619143.00, 273174373766.00, 230758287240.52, 201962265474.48, 21917549055.74, 23897523427.36, 19846347957.99, 20050539940.88, 19254914794.05, 19543371812.31, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 124510246988.33, 121042691016.62);

CREATE TEMP TABLE actual_amount_totals AS
SELECT
    ano_eje,
    SUM(monto_pia)::NUMERIC(38, 2) AS monto_pia,
    SUM(monto_pim)::NUMERIC(38, 2) AS monto_pim,
    SUM(monto_certificado_anual)::NUMERIC(38, 2) AS monto_certificado_anual,
    SUM(monto_comprometido_anual)::NUMERIC(38, 2) AS monto_comprometido_anual,
    SUM(monto_devengado_enero)::NUMERIC(38, 2) AS monto_devengado_enero,
    SUM(monto_devengado_febrero)::NUMERIC(38, 2) AS monto_devengado_febrero,
    SUM(monto_devengado_marzo)::NUMERIC(38, 2) AS monto_devengado_marzo,
    SUM(monto_devengado_abril)::NUMERIC(38, 2) AS monto_devengado_abril,
    SUM(monto_devengado_mayo)::NUMERIC(38, 2) AS monto_devengado_mayo,
    SUM(monto_devengado_junio)::NUMERIC(38, 2) AS monto_devengado_junio,
    SUM(monto_devengado_julio)::NUMERIC(38, 2) AS monto_devengado_julio,
    SUM(monto_devengado_agosto)::NUMERIC(38, 2) AS monto_devengado_agosto,
    SUM(monto_devengado_septiembre)::NUMERIC(38, 2) AS monto_devengado_septiembre,
    SUM(monto_devengado_octubre)::NUMERIC(38, 2) AS monto_devengado_octubre,
    SUM(monto_devengado_noviembre)::NUMERIC(38, 2) AS monto_devengado_noviembre,
    SUM(monto_devengado_diciembre)::NUMERIC(38, 2) AS monto_devengado_diciembre,
    SUM(monto_devengado_anual)::NUMERIC(38, 2) AS monto_devengado_anual,
    SUM(monto_girado_anual)::NUMERIC(38, 2) AS monto_girado_anual
FROM staging.mef_devengado
GROUP BY ano_eje;

CREATE TEMP TABLE amount_total_comparison AS
SELECT
    expected.ano_eje,
    comparison.measure_name,
    comparison.expected_total,
    comparison.actual_total,
    (
        comparison.actual_total
        - comparison.expected_total
    )::NUMERIC(38, 2) AS difference
FROM expected_amount_totals AS expected
JOIN actual_amount_totals AS actual
    USING (ano_eje)
CROSS JOIN LATERAL (
    VALUES
        ('MONTO_PIA', expected.monto_pia, actual.monto_pia),
        ('MONTO_PIM', expected.monto_pim, actual.monto_pim),
        ('MONTO_CERTIFICADO_ANUAL', expected.monto_certificado_anual, actual.monto_certificado_anual),
        ('MONTO_COMPROMETIDO_ANUAL', expected.monto_comprometido_anual, actual.monto_comprometido_anual),
        ('MONTO_DEVENGADO_ENERO', expected.monto_devengado_enero, actual.monto_devengado_enero),
        ('MONTO_DEVENGADO_FEBRERO', expected.monto_devengado_febrero, actual.monto_devengado_febrero),
        ('MONTO_DEVENGADO_MARZO', expected.monto_devengado_marzo, actual.monto_devengado_marzo),
        ('MONTO_DEVENGADO_ABRIL', expected.monto_devengado_abril, actual.monto_devengado_abril),
        ('MONTO_DEVENGADO_MAYO', expected.monto_devengado_mayo, actual.monto_devengado_mayo),
        ('MONTO_DEVENGADO_JUNIO', expected.monto_devengado_junio, actual.monto_devengado_junio),
        ('MONTO_DEVENGADO_JULIO', expected.monto_devengado_julio, actual.monto_devengado_julio),
        ('MONTO_DEVENGADO_AGOSTO', expected.monto_devengado_agosto, actual.monto_devengado_agosto),
        ('MONTO_DEVENGADO_SEPTIEMBRE', expected.monto_devengado_septiembre, actual.monto_devengado_septiembre),
        ('MONTO_DEVENGADO_OCTUBRE', expected.monto_devengado_octubre, actual.monto_devengado_octubre),
        ('MONTO_DEVENGADO_NOVIEMBRE', expected.monto_devengado_noviembre, actual.monto_devengado_noviembre),
        ('MONTO_DEVENGADO_DICIEMBRE', expected.monto_devengado_diciembre, actual.monto_devengado_diciembre),
        ('MONTO_DEVENGADO_ANUAL', expected.monto_devengado_anual, actual.monto_devengado_anual),
        ('MONTO_GIRADO_ANUAL', expected.monto_girado_anual, actual.monto_girado_anual)
) AS comparison(
    measure_name,
    expected_total,
    actual_total
);

\echo 'Diferencias monetarias exactas'

SELECT
    ano_eje,
    measure_name,
    expected_total,
    actual_total,
    difference
FROM amount_total_comparison
WHERE difference <> 0
ORDER BY ano_eje, measure_name;

\echo 'Resumen de reconciliación exacta por año'

SELECT
    ano_eje,
    COUNT(*) AS measures_checked,
    COUNT(*) FILTER (
        WHERE difference = 0
    ) AS exact_matches,
    MAX(
        ABS(difference)
    ) AS maximum_absolute_difference
FROM amount_total_comparison
GROUP BY ano_eje
ORDER BY ano_eje;

DO $$
DECLARE
    year_count INTEGER;
    comparison_count INTEGER;
    mismatch_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO year_count
    FROM actual_amount_totals;

    SELECT COUNT(*)
    INTO comparison_count
    FROM amount_total_comparison;

    SELECT COUNT(*)
    INTO mismatch_count
    FROM amount_total_comparison
    WHERE difference <> 0;

    IF year_count <> 3 THEN
        RAISE EXCEPTION
            'Cantidad de años inesperada: %, esperado: 3',
            year_count;
    END IF;

    IF comparison_count <> 54 THEN
        RAISE EXCEPTION
            'Cantidad de comparaciones inesperada: %, esperado: 54',
            comparison_count;
    END IF;

    IF mismatch_count <> 0 THEN
        RAISE EXCEPTION
            'Se encontraron % diferencias monetarias exactas',
            mismatch_count;
    END IF;
END
$$;

COMMIT;

\echo 'Las 54 comparaciones monetarias coinciden exactamente.'
