"""Pruebas unitarias para el perfilado estructural."""

from __future__ import annotations

from src.profile_sources import (
    classify_devengado_columns,
    compare_schemas,
)


def test_classify_devengado_columns() -> None:
    """Debe separar los meses de la columna anual."""
    columns = [
        "ANO_EJE",
        "MONTO_DEVENGADO_ENERO",
        "MONTO_DEVENGADO_FEBRERO",
        "MONTO_DEVENGADO_ANUAL",
    ]

    monthly, annual, other = classify_devengado_columns(columns)

    assert monthly == [
        "MONTO_DEVENGADO_ENERO",
        "MONTO_DEVENGADO_FEBRERO",
    ]
    assert annual == ["MONTO_DEVENGADO_ANUAL"]
    assert other == []


def test_compare_schemas_accepts_equal_schemas() -> None:
    """Dos esquemas iguales deben coincidir en cantidad, nombres y orden."""
    reports = [
        {
            "source_id": "source_2024",
            "columns": ["A", "B", "C"],
        },
        {
            "source_id": "source_2025",
            "columns": ["A", "B", "C"],
        },
    ]

    result = compare_schemas(reports)

    assert result["all_same_column_count"] is True
    assert result["all_same_column_names"] is True
    assert result["all_same_column_order"] is True


def test_compare_schemas_detects_different_order() -> None:
    """Debe detectar columnas iguales colocadas en distinto orden."""
    reports = [
        {
            "source_id": "source_2024",
            "columns": ["A", "B", "C"],
        },
        {
            "source_id": "source_2025",
            "columns": ["B", "A", "C"],
        },
    ]

    result = compare_schemas(reports)

    assert result["all_same_column_count"] is True
    assert result["all_same_column_names"] is True
    assert result["all_same_column_order"] is False


def test_compare_schemas_detects_missing_and_additional() -> None:
    """Debe registrar columnas faltantes y adicionales."""
    reports = [
        {
            "source_id": "source_2024",
            "columns": ["A", "B", "C"],
        },
        {
            "source_id": "source_2025",
            "columns": ["A", "B", "D"],
        },
    ]

    result = compare_schemas(reports)
    comparison = result["comparisons"][1]

    assert result["all_same_column_names"] is False
    assert comparison["missing_columns_vs_base"] == ["C"]
    assert comparison["additional_columns_vs_base"] == ["D"]