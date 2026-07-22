BEGIN;

CREATE SCHEMA IF NOT EXISTS staging
    AUTHORIZATION budget_app;

CREATE SCHEMA IF NOT EXISTS analytics
    AUTHORIZATION budget_app;

COMMENT ON SCHEMA staging IS
    'Capa de recepción y validación de los datos consolidados del MEF.';

COMMENT ON SCHEMA analytics IS
    'Capa destinada al modelo analítico y consultas del proyecto.';

COMMIT;