"""Pruebas de los contratos SQL de PostgreSQL."""

from __future__ import annotations

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SQL_DIRECTORY = PROJECT_ROOT / "sql"


def read_sql(filename: str) -> str:
    """Lee un script SQL versionado."""
    return (
        SQL_DIRECTORY
        / filename
    ).read_text(
        encoding="utf-8",
    )


def test_staging_table_has_expected_columns_and_types() -> None:
    """La tabla staging debe conservar las 73 columnas."""
    sql = read_sql(
        "002_create_staging_table.sql"
    )

    match = re.search(
        (
            r"CREATE TABLE IF NOT EXISTS "
            r"staging\.mef_devengado\s*\("
            r"(?P<body>.*?)"
            r"\n\);"
        ),
        sql,
        flags=re.DOTALL,
    )

    assert match is not None

    definitions = [
        line.strip().rstrip(",")
        for line in match.group("body").splitlines()
        if line.strip()
    ]

    numeric_definitions = [
        definition
        for definition in definitions
        if (
            "NUMERIC(24, 2) "
            "NOT NULL DEFAULT 0"
        ) in definition
    ]

    assert len(definitions) == 73
    assert len(numeric_definitions) == 18
    assert (
        "ano_eje SMALLINT NOT NULL"
        in definitions
    )


def test_load_script_covers_all_periods() -> None:
    """La carga debe incluir y validar los tres años."""
    sql = read_sql(
        "003_load_staging.sql"
    )

    expected_periods = {
        2024: 2_789_605,
        2025: 2_807_021,
        2026: 2_101_614,
    }

    assert (
        sql.count(
            r"\copy staging.mef_devengado FROM"
        )
        == 3
    )

    for year, expected_count in (
        expected_periods.items()
    ):
        assert (
            f"mef_devengado_{year}"
            "_consolidated.csv"
        ) in sql

        assert str(expected_count) in sql

    assert "7698240" in sql

    assert (
        "CREATE INDEX "
        "idx_mef_devengado_ano_eje_brin"
    ) in sql


def test_amount_reconciliation_requires_exact_matches() -> None:
    """La reconciliación final no debe usar tolerancias."""
    sql = read_sql(
        "005_validate_amount_totals.sql"
    )

    assert "WHERE difference <> 0" in sql

    assert (
        "Las 54 comparaciones monetarias "
        "coinciden exactamente."
    ) in sql

    assert "ABS(difference) > 0.01" not in sql
    assert "tolerancia de S/ 0.01" not in sql


def test_environment_example_contains_no_real_secret() -> None:
    """La plantilla debe usar una contraseña de ejemplo."""
    content = (
        PROJECT_ROOT
        / ".env.example"
    ).read_text(
        encoding="utf-8",
    )

    assert "PGHOST=127.0.0.1" in content
    assert "PGPORT=5432" in content
    assert (
        "PGDATABASE=peru_public_budget"
        in content
    )
    assert "PGUSER=budget_app" in content

    assert (
        "PGPASSWORD="
        "REEMPLAZAR_EN_EL_ARCHIVO_ENV_LOCAL"
    ) in content