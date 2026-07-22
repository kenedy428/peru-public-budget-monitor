#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/.."
    pwd
)"

ENV_FILE="${PROJECT_ROOT}/.env"

if [[ ! -f "${ENV_FILE}" ]]; then
    echo "No existe ${ENV_FILE}."
    echo "Créalo copiando .env.example y completa las credenciales."
    exit 1
fi

set -a

# shellcheck disable=SC1090
source "${ENV_FILE}"

set +a

required_variables=(
    PGHOST
    PGPORT
    PGDATABASE
    PGUSER
    PGPASSWORD
)

for variable_name in "${required_variables[@]}"; do
    if [[ -z "${!variable_name:-}" ]]; then
        echo "Falta la variable ${variable_name} en .env."
        exit 1
    fi
done

exec psql \
    -v ON_ERROR_STOP=1 \
    "$@"