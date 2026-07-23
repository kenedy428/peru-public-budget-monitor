\set ON_ERROR_STOP on
\timing on

-- ============================================================
-- Índices de la tabla de hechos
-- ============================================================

\echo '1. Creando índice BRIN para el tiempo'

CREATE INDEX IF NOT EXISTS
    idx_fact_ejecucion_tiempo_brin
ON analytics.fact_ejecucion_presupuestal
USING BRIN (
    tiempo_key
)
WITH (
    pages_per_range = 128
);

\echo '2. Creando índices B-tree dimensionales'

CREATE INDEX IF NOT EXISTS
    idx_fact_ejecucion_institucion
ON analytics.fact_ejecucion_presupuestal (
    institucion_key
);

CREATE INDEX IF NOT EXISTS
    idx_fact_ejecucion_meta
ON analytics.fact_ejecucion_presupuestal (
    meta_presupuestaria_key
);

CREATE INDEX IF NOT EXISTS
    idx_fact_ejecucion_funcional
ON analytics.fact_ejecucion_presupuestal (
    funcional_key
);

CREATE INDEX IF NOT EXISTS
    idx_fact_ejecucion_financiamiento
ON analytics.fact_ejecucion_presupuestal (
    financiamiento_key
);

CREATE INDEX IF NOT EXISTS
    idx_fact_ejecucion_clasificador
ON analytics.fact_ejecucion_presupuestal (
    clasificador_gasto_key
);

CREATE INDEX IF NOT EXISTS
    idx_fact_ejecucion_ubicacion
ON analytics.fact_ejecucion_presupuestal (
    ubicacion_ejecutora_key
);

CREATE INDEX IF NOT EXISTS
    idx_fact_ejecucion_departamento_meta
ON analytics.fact_ejecucion_presupuestal (
    departamento_meta_key
);

-- ============================================================
-- Claves foráneas
-- Se crean primero como NOT VALID para separar la definición
-- de la validación completa de las 7.7 millones de filas.
-- ============================================================

\echo '3. Creando claves foráneas'

DO $$
DECLARE
    item RECORD;
BEGIN
    FOR item IN
        SELECT *
        FROM (
            VALUES
                (
                    'fk_fact_tiempo',
                    'tiempo_key',
                    'dim_tiempo',
                    'tiempo_key'
                ),
                (
                    'fk_fact_institucion',
                    'institucion_key',
                    'dim_institucion',
                    'institucion_key'
                ),
                (
                    'fk_fact_meta_presupuestaria',
                    'meta_presupuestaria_key',
                    'dim_meta_presupuestaria',
                    'meta_presupuestaria_key'
                ),
                (
                    'fk_fact_funcional',
                    'funcional_key',
                    'dim_funcional',
                    'funcional_key'
                ),
                (
                    'fk_fact_financiamiento',
                    'financiamiento_key',
                    'dim_financiamiento',
                    'financiamiento_key'
                ),
                (
                    'fk_fact_clasificador_gasto',
                    'clasificador_gasto_key',
                    'dim_clasificador_gasto',
                    'clasificador_gasto_key'
                ),
                (
                    'fk_fact_ubicacion_ejecutora',
                    'ubicacion_ejecutora_key',
                    'dim_ubicacion_ejecutora',
                    'ubicacion_ejecutora_key'
                ),
                (
                    'fk_fact_departamento_meta',
                    'departamento_meta_key',
                    'dim_departamento_meta',
                    'departamento_meta_key'
                )
        ) AS constraints_to_create (
            constraint_name,
            fact_column,
            dimension_table,
            dimension_column
        )
    LOOP
        IF NOT EXISTS (
            SELECT 1
            FROM pg_constraint AS constraint_definition
            JOIN pg_class AS relation
                ON relation.oid =
                    constraint_definition.conrelid
            JOIN pg_namespace AS namespace
                ON namespace.oid =
                    relation.relnamespace
            WHERE namespace.nspname = 'analytics'
              AND relation.relname =
                  'fact_ejecucion_presupuestal'
              AND constraint_definition.conname =
                  item.constraint_name
        ) THEN
            EXECUTE FORMAT(
                'ALTER TABLE '
                'analytics.fact_ejecucion_presupuestal '
                'ADD CONSTRAINT %I '
                'FOREIGN KEY (%I) '
                'REFERENCES analytics.%I (%I) '
                'NOT VALID',
                item.constraint_name,
                item.fact_column,
                item.dimension_table,
                item.dimension_column
            );
        END IF;
    END LOOP;
END;
$$;

-- ============================================================
-- Validación física de las claves foráneas
-- ============================================================

\echo '4. Validando claves foráneas'

DO $$
DECLARE
    item RECORD;
BEGIN
    FOR item IN
        SELECT
            constraint_definition.conname
        FROM pg_constraint AS constraint_definition
        JOIN pg_class AS relation
            ON relation.oid =
                constraint_definition.conrelid
        JOIN pg_namespace AS namespace
            ON namespace.oid =
                relation.relnamespace
        WHERE namespace.nspname = 'analytics'
          AND relation.relname =
              'fact_ejecucion_presupuestal'
          AND constraint_definition.contype = 'f'
          AND NOT constraint_definition.convalidated
        ORDER BY constraint_definition.conname
    LOOP
        RAISE NOTICE
            'Validando restricción %.',
            item.conname;

        EXECUTE FORMAT(
            'ALTER TABLE '
            'analytics.fact_ejecucion_presupuestal '
            'VALIDATE CONSTRAINT %I',
            item.conname
        );
    END LOOP;
END;
$$;

-- ============================================================
-- Control final
-- ============================================================

\echo '5. Verificando restricciones relacionales'

DO $$
DECLARE
    foreign_key_count INTEGER;
    invalid_foreign_key_count INTEGER;
BEGIN
    SELECT
        COUNT(*),
        COUNT(*) FILTER (
            WHERE NOT constraint_definition.convalidated
        )
    INTO
        foreign_key_count,
        invalid_foreign_key_count
    FROM pg_constraint AS constraint_definition
    JOIN pg_class AS relation
        ON relation.oid =
            constraint_definition.conrelid
    JOIN pg_namespace AS namespace
        ON namespace.oid =
            relation.relnamespace
    WHERE namespace.nspname = 'analytics'
      AND relation.relname =
          'fact_ejecucion_presupuestal'
      AND constraint_definition.contype = 'f';

    IF foreign_key_count <> 8 THEN
        RAISE EXCEPTION
            'Se esperaban 8 claves foráneas y se encontraron %.',
            foreign_key_count;
    END IF;

    IF invalid_foreign_key_count <> 0 THEN
        RAISE EXCEPTION
            'Existen % claves foráneas sin validar.',
            invalid_foreign_key_count;
    END IF;

    RAISE NOTICE
        'Las ocho claves foráneas están creadas y validadas.';
END;
$$;

ANALYZE
    analytics.fact_ejecucion_presupuestal;

\echo '6. Índices de la tabla de hechos'

SELECT
    indexname,
    pg_size_pretty(
        pg_relation_size(
            (
                schemaname
                || '.'
                || indexname
            )::REGCLASS
        )
    ) AS index_size
FROM pg_indexes
WHERE schemaname = 'analytics'
  AND tablename =
      'fact_ejecucion_presupuestal'
ORDER BY indexname;

\echo '7. Claves foráneas de la tabla de hechos'

SELECT
    constraint_definition.conname
        AS constraint_name,
    constraint_definition.convalidated
        AS validated
FROM pg_constraint AS constraint_definition
JOIN pg_class AS relation
    ON relation.oid =
        constraint_definition.conrelid
JOIN pg_namespace AS namespace
    ON namespace.oid =
        relation.relnamespace
WHERE namespace.nspname = 'analytics'
  AND relation.relname =
      'fact_ejecucion_presupuestal'
  AND constraint_definition.contype = 'f'
ORDER BY constraint_definition.conname;

\echo '8. Tamaño físico del modelo analytics'

SELECT
    pg_size_pretty(
        pg_relation_size(
            'analytics.fact_ejecucion_presupuestal'
        )
    ) AS fact_table_size,

    pg_size_pretty(
        pg_indexes_size(
            'analytics.fact_ejecucion_presupuestal'
        )
    ) AS fact_indexes_size,

    pg_size_pretty(
        pg_total_relation_size(
            'analytics.fact_ejecucion_presupuestal'
        )
    ) AS fact_total_size;

\echo 'Modelo analytics finalizado correctamente.'