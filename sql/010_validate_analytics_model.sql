\set ON_ERROR_STOP on
\timing on

\echo '1. Tablas del esquema analytics'

SELECT
    table_name
FROM information_schema.tables
WHERE table_schema = 'analytics'
  AND table_type = 'BASE TABLE'
ORDER BY table_name;

\echo '2. Cantidad de tablas'

DO $$
DECLARE
    actual_table_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO actual_table_count
    FROM information_schema.tables
    WHERE table_schema = 'analytics'
      AND table_type = 'BASE TABLE';

    IF actual_table_count <> 9 THEN
        RAISE EXCEPTION
            'Se esperaban 9 tablas y se encontraron %.',
            actual_table_count;
    END IF;

    RAISE NOTICE
        'Cantidad de tablas correcta: %.',
        actual_table_count;
END;
$$;

\echo '3. Cantidad de columnas por tabla'

SELECT
    table_name,
    COUNT(*) AS column_count
FROM information_schema.columns
WHERE table_schema = 'analytics'
GROUP BY table_name
ORDER BY table_name;

\echo '4. Validación de las 18 medidas monetarias'

DO $$
DECLARE
    actual_measure_count INTEGER;
    invalid_measure_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO actual_measure_count
    FROM information_schema.columns
    WHERE table_schema = 'analytics'
      AND table_name = 'fact_ejecucion_presupuestal'
      AND column_name LIKE 'monto_%';

    SELECT COUNT(*)
    INTO invalid_measure_count
    FROM information_schema.columns
    WHERE table_schema = 'analytics'
      AND table_name = 'fact_ejecucion_presupuestal'
      AND column_name LIKE 'monto_%'
      AND (
          data_type <> 'numeric'
          OR numeric_precision <> 24
          OR numeric_scale <> 2
          OR is_nullable <> 'NO'
      );

    IF actual_measure_count <> 18 THEN
        RAISE EXCEPTION
            'Se esperaban 18 medidas y se encontraron %.',
            actual_measure_count;
    END IF;

    IF invalid_measure_count <> 0 THEN
        RAISE EXCEPTION
            'Se encontraron % medidas con definición incorrecta.',
            invalid_measure_count;
    END IF;

    RAISE NOTICE
        'Las 18 medidas utilizan NUMERIC(24,2) NOT NULL.';
END;
$$;

\echo '5. Claves primarias'

SELECT
    table_name,
    constraint_name
FROM information_schema.table_constraints
WHERE constraint_schema = 'analytics'
  AND constraint_type = 'PRIMARY KEY'
ORDER BY table_name;

\echo '6. Restricciones únicas naturales'

SELECT
    table_name,
    constraint_name
FROM information_schema.table_constraints
WHERE constraint_schema = 'analytics'
  AND constraint_type = 'UNIQUE'
ORDER BY table_name;

\echo '7. Columnas identity de las dimensiones'

SELECT
    table_name,
    column_name,
    identity_generation
FROM information_schema.columns
WHERE table_schema = 'analytics'
  AND is_identity = 'YES'
ORDER BY table_name;

\echo '8. Confirmación de tablas vacías antes de la carga'

DO $$
DECLARE
    populated_tables TEXT[];
BEGIN
    SELECT ARRAY_AGG(
        table_name
        ORDER BY table_name
    )
    INTO populated_tables
    FROM (
        SELECT
            'analytics.dim_tiempo'::TEXT
                AS table_name
        WHERE EXISTS (
            SELECT 1
            FROM analytics.dim_tiempo
        )

        UNION ALL

        SELECT
            'analytics.dim_institucion'
        WHERE EXISTS (
            SELECT 1
            FROM analytics.dim_institucion
        )

        UNION ALL

        SELECT
            'analytics.dim_meta_presupuestaria'
        WHERE EXISTS (
            SELECT 1
            FROM analytics.dim_meta_presupuestaria
        )

        UNION ALL

        SELECT
            'analytics.dim_funcional'
        WHERE EXISTS (
            SELECT 1
            FROM analytics.dim_funcional
        )

        UNION ALL

        SELECT
            'analytics.dim_financiamiento'
        WHERE EXISTS (
            SELECT 1
            FROM analytics.dim_financiamiento
        )

        UNION ALL

        SELECT
            'analytics.dim_clasificador_gasto'
        WHERE EXISTS (
            SELECT 1
            FROM analytics.dim_clasificador_gasto
        )

        UNION ALL

        SELECT
            'analytics.dim_ubicacion_ejecutora'
        WHERE EXISTS (
            SELECT 1
            FROM analytics.dim_ubicacion_ejecutora
        )

        UNION ALL

        SELECT
            'analytics.dim_departamento_meta'
        WHERE EXISTS (
            SELECT 1
            FROM analytics.dim_departamento_meta
        )

        UNION ALL

        SELECT
            'analytics.fact_ejecucion_presupuestal'
        WHERE EXISTS (
            SELECT 1
            FROM analytics.fact_ejecucion_presupuestal
        )
    ) AS table_status;

    IF populated_tables IS NOT NULL THEN
        RAISE EXCEPTION
            'Las siguientes tablas ya contienen registros: %.',
            ARRAY_TO_STRING(
                populated_tables,
                ', '
            );
    END IF;

    RAISE NOTICE
        'Las nueve tablas están vacías y listas para la carga.';
END;
$$;

\echo 'Validación estructural completada correctamente.'