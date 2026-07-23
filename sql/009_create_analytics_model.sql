\set ON_ERROR_STOP on
\timing on

BEGIN;

CREATE SCHEMA IF NOT EXISTS analytics;

-- ============================================================
-- Dimensión de tiempo
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.dim_tiempo (
    tiempo_key SMALLINT
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    ano_eje SMALLINT NOT NULL,

    CONSTRAINT uq_dim_tiempo_ano_eje
        UNIQUE (ano_eje)
);

COMMENT ON TABLE analytics.dim_tiempo IS
    'Años de ejecución presupuestal disponibles en el modelo analítico.';

-- ============================================================
-- Dimensión institucional
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.dim_institucion (
    institucion_key INTEGER
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    ano_eje SMALLINT NOT NULL,
    sec_ejec TEXT NOT NULL,

    nivel_gobierno TEXT NOT NULL,
    nivel_gobierno_nombre TEXT NOT NULL,

    sector TEXT,
    sector_nombre TEXT,

    pliego TEXT,
    pliego_nombre TEXT,

    ejecutora TEXT NOT NULL,
    ejecutora_nombre TEXT NOT NULL,

    CONSTRAINT uq_dim_institucion_natural
        UNIQUE (
            ano_eje,
            sec_ejec
        )
);

COMMENT ON TABLE analytics.dim_institucion IS
    'Versión anual de las entidades, pliegos, sectores y niveles de gobierno.';

-- ============================================================
-- Dimensión de meta presupuestaria
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.dim_meta_presupuestaria (
    meta_presupuestaria_key INTEGER
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    ano_eje SMALLINT NOT NULL,
    sec_ejec TEXT NOT NULL,
    sec_func TEXT NOT NULL,

    programa_ppto TEXT NOT NULL,
    programa_ppto_nombre TEXT NOT NULL,

    tipo_act_proy TEXT NOT NULL,

    producto_proyecto TEXT NOT NULL,
    producto_proyecto_nombre TEXT NOT NULL,

    actividad_accion_obra TEXT NOT NULL,
    actividad_accion_obra_nombre TEXT NOT NULL,

    meta TEXT NOT NULL,
    finalidad TEXT NOT NULL,
    meta_nombre TEXT,

    CONSTRAINT uq_dim_meta_presupuestaria_natural
        UNIQUE (
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
);

COMMENT ON TABLE analytics.dim_meta_presupuestaria IS
    'Cadena programática completa y finalidad de cada meta presupuestaria.';

-- ============================================================
-- Dimensión funcional
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.dim_funcional (
    funcional_key INTEGER
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    funcion TEXT NOT NULL,
    funcion_nombre TEXT NOT NULL,

    division_funcional TEXT NOT NULL,
    division_funcional_nombre TEXT NOT NULL,

    grupo_funcional TEXT NOT NULL,
    grupo_funcional_nombre TEXT NOT NULL,

    CONSTRAINT uq_dim_funcional_natural
        UNIQUE (
            funcion,
            division_funcional,
            grupo_funcional
        )
);

COMMENT ON TABLE analytics.dim_funcional IS
    'Clasificación funcional del gasto público.';

-- ============================================================
-- Dimensión de financiamiento
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.dim_financiamiento (
    financiamiento_key INTEGER
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    fuente_financiamiento TEXT NOT NULL,
    fuente_financiamiento_nombre TEXT NOT NULL,

    rubro TEXT NOT NULL,
    rubro_nombre TEXT NOT NULL,

    tipo_recurso TEXT NOT NULL,
    tipo_recurso_nombre TEXT NOT NULL,

    CONSTRAINT uq_dim_financiamiento_natural
        UNIQUE (
            fuente_financiamiento,
            rubro,
            tipo_recurso
        )
);

COMMENT ON TABLE analytics.dim_financiamiento IS
    'Fuente de financiamiento, rubro y tipo de recurso presupuestal.';

-- ============================================================
-- Dimensión del clasificador de gasto
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.dim_clasificador_gasto (
    clasificador_gasto_key INTEGER
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    ano_eje SMALLINT NOT NULL,

    categoria_gasto TEXT NOT NULL,
    categoria_gasto_nombre TEXT NOT NULL,

    tipo_transaccion TEXT NOT NULL,
    tipo_transaccion_nombre TEXT NOT NULL,

    generica TEXT NOT NULL,
    generica_nombre TEXT NOT NULL,

    subgenerica TEXT NOT NULL,
    subgenerica_nombre TEXT NOT NULL,

    subgenerica_det TEXT NOT NULL,
    subgenerica_det_nombre TEXT NOT NULL,

    especifica TEXT NOT NULL,
    especifica_nombre TEXT NOT NULL,

    especifica_det TEXT NOT NULL,
    especifica_det_nombre TEXT NOT NULL,

    CONSTRAINT uq_dim_clasificador_gasto_natural
        UNIQUE (
            ano_eje,
            categoria_gasto,
            tipo_transaccion,
            generica,
            subgenerica,
            subgenerica_det,
            especifica,
            especifica_det
        )
);

COMMENT ON TABLE analytics.dim_clasificador_gasto IS
    'Versión anual de la cadena completa del clasificador de gasto.';

-- ============================================================
-- Dimensión de ubicación de la ejecutora
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.dim_ubicacion_ejecutora (
    ubicacion_ejecutora_key INTEGER
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    departamento_ejecutora TEXT NOT NULL,
    departamento_ejecutora_nombre TEXT NOT NULL,

    provincia_ejecutora TEXT NOT NULL,
    provincia_ejecutora_nombre TEXT NOT NULL,

    distrito_ejecutora TEXT NOT NULL,
    distrito_ejecutora_nombre TEXT NOT NULL,

    CONSTRAINT uq_dim_ubicacion_ejecutora_natural
        UNIQUE (
            departamento_ejecutora,
            provincia_ejecutora,
            distrito_ejecutora
        )
);

COMMENT ON TABLE analytics.dim_ubicacion_ejecutora IS
    'Ubicación geográfica de las unidades ejecutoras.';

-- ============================================================
-- Dimensión del departamento de la meta
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.dim_departamento_meta (
    departamento_meta_key INTEGER
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    departamento_meta TEXT NOT NULL,

    -- Valor original proporcionado por la fuente.
    -- Puede ser nulo cuando departamento_meta = '0'.
    departamento_meta_nombre TEXT,

    -- Etiqueta destinada al consumo analítico y Power BI.
    departamento_meta_nombre_analitico TEXT
        GENERATED ALWAYS AS (
            COALESCE(
                departamento_meta_nombre,
                'NO ESPECIFICADO'
            )
        ) STORED,

    CONSTRAINT uq_dim_departamento_meta_natural
        UNIQUE (departamento_meta)
);

-- Permite actualizar una tabla creada con una versión anterior
-- del DDL sin tener que eliminarla manualmente.
ALTER TABLE analytics.dim_departamento_meta
    ALTER COLUMN departamento_meta_nombre
    DROP NOT NULL;

ALTER TABLE analytics.dim_departamento_meta
    ADD COLUMN IF NOT EXISTS
        departamento_meta_nombre_analitico TEXT
        GENERATED ALWAYS AS (
            COALESCE(
                departamento_meta_nombre,
                'NO ESPECIFICADO'
            )
        ) STORED;

COMMENT ON TABLE analytics.dim_departamento_meta IS
    'Departamento donde se ejecuta la meta presupuestaria.';

COMMENT ON COLUMN
    analytics.dim_departamento_meta.departamento_meta_nombre
IS
    'Nombre original de la fuente; puede ser nulo para el código 0.';

COMMENT ON COLUMN
    analytics.dim_departamento_meta.departamento_meta_nombre_analitico
IS
    'Etiqueta analítica derivada; sustituye nombres nulos por NO ESPECIFICADO.';

-- ============================================================
-- Tabla de hechos
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.fact_ejecucion_presupuestal (
    tiempo_key SMALLINT NOT NULL,
    institucion_key INTEGER NOT NULL,
    meta_presupuestaria_key INTEGER NOT NULL,
    funcional_key INTEGER NOT NULL,
    financiamiento_key INTEGER NOT NULL,
    clasificador_gasto_key INTEGER NOT NULL,
    ubicacion_ejecutora_key INTEGER NOT NULL,
    departamento_meta_key INTEGER NOT NULL,

    monto_pia NUMERIC(24, 2) NOT NULL,
    monto_pim NUMERIC(24, 2) NOT NULL,

    monto_certificado_anual NUMERIC(24, 2) NOT NULL,
    monto_comprometido_anual NUMERIC(24, 2) NOT NULL,

    monto_devengado_enero NUMERIC(24, 2) NOT NULL,
    monto_devengado_febrero NUMERIC(24, 2) NOT NULL,
    monto_devengado_marzo NUMERIC(24, 2) NOT NULL,
    monto_devengado_abril NUMERIC(24, 2) NOT NULL,
    monto_devengado_mayo NUMERIC(24, 2) NOT NULL,
    monto_devengado_junio NUMERIC(24, 2) NOT NULL,
    monto_devengado_julio NUMERIC(24, 2) NOT NULL,
    monto_devengado_agosto NUMERIC(24, 2) NOT NULL,
    monto_devengado_septiembre NUMERIC(24, 2) NOT NULL,
    monto_devengado_octubre NUMERIC(24, 2) NOT NULL,
    monto_devengado_noviembre NUMERIC(24, 2) NOT NULL,
    monto_devengado_diciembre NUMERIC(24, 2) NOT NULL,

    monto_devengado_anual NUMERIC(24, 2) NOT NULL,
    monto_girado_anual NUMERIC(24, 2) NOT NULL
);

COMMENT ON TABLE analytics.fact_ejecucion_presupuestal IS
    'Hechos presupuestales del MEF vinculados con las dimensiones analíticas.';

COMMIT;