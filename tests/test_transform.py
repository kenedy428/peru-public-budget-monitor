"""Pruebas de transformación y consolidación."""

from __future__ import annotations

import pandas as pd
import pytest

from src.transform import (
    consolidate_dataframe,
    identify_measure_columns,
)


def test_identify_measure_columns() -> None:
    """Debe identificar únicamente las medidas monetarias."""
    columns = [
        "ANO_EJE",
        "EJECUTORA",
        "MONTO_PIA",
        "MONTO_PIM",
        "META_NOMBRE",
    ]

    result = identify_measure_columns(columns)

    assert result == [
        "MONTO_PIA",
        "MONTO_PIM",
    ]


def test_consolidate_dataframe_sums_split_measures() -> None:
    """Debe consolidar montos distribuidos entre varias filas."""
    frame = pd.DataFrame(
        [
            {
                "ANO_EJE": "2026",
                "EJECUTORA": "001",
                "META": "10",
                "META_NOMBRE": " Meta de prueba ",
                "MONTO_PIM": "100",
                "MONTO_CERTIFICADO_ANUAL": "0",
            },
            {
                "ANO_EJE": "2026",
                "EJECUTORA": "001",
                "META": "10",
                "META_NOMBRE": "Meta de prueba",
                "MONTO_PIM": "0",
                "MONTO_CERTIFICADO_ANUAL": "80",
            },
            {
                "ANO_EJE": "2026",
                "EJECUTORA": "002",
                "META": "20",
                "META_NOMBRE": "Otra meta",
                "MONTO_PIM": "50",
                "MONTO_CERTIFICADO_ANUAL": "25",
            },
        ]
    )

    consolidated, report = consolidate_dataframe(
        frame=frame,
        key_columns=(
            "ANO_EJE",
            "EJECUTORA",
            "META",
        ),
        measure_columns=(
            "MONTO_PIM",
            "MONTO_CERTIFICADO_ANUAL",
        ),
    )

    assert len(consolidated) == 2

    first_row = consolidated.loc[
        consolidated["EJECUTORA"].eq("001")
    ].iloc[0]

    assert first_row["META_NOMBRE"] == "Meta de prueba"
    assert first_row["MONTO_PIM"] == 100
    assert (
        first_row["MONTO_CERTIFICADO_ANUAL"]
        == 80
    )

    assert report["row_count_before"] == 3
    assert (
        report["row_count_after_consolidation"]
        == 2
    )
    assert report["rows_consolidated"] == 1
    assert report["totals_preserved"] is True
    assert report["measure_total_differences"] == {
        "MONTO_PIM": 0.0,
        "MONTO_CERTIFICADO_ANUAL": 0.0,
    }


def test_consolidate_dataframe_removes_exact_duplicates() -> None:
    """Debe eliminar filas completamente idénticas."""
    frame = pd.DataFrame(
        [
            {
                "KEY": "A",
                "DESCRIPTION": "Registro",
                "MONTO_PIM": "0",
            },
            {
                "KEY": "A",
                "DESCRIPTION": "Registro",
                "MONTO_PIM": "0",
            },
        ]
    )

    consolidated, report = consolidate_dataframe(
        frame=frame,
        key_columns=("KEY",),
        measure_columns=("MONTO_PIM",),
    )

    assert len(consolidated) == 1
    assert report["exact_duplicate_rows_removed"] == 1
    assert report["rows_consolidated"] == 0
    assert report["totals_preserved"] is True


def test_consolidate_dataframe_rejects_inconsistent_attributes() -> None:
    """Debe rechazar descripciones distintas para la misma clave."""
    frame = pd.DataFrame(
        [
            {
                "KEY": "A",
                "DESCRIPTION": "Descripción uno",
                "MONTO_PIM": "10",
            },
            {
                "KEY": "A",
                "DESCRIPTION": "Descripción dos",
                "MONTO_PIM": "0",
            },
        ]
    )

    with pytest.raises(
        ValueError,
        match="atributos no monetarios inconsistentes",
    ):
        consolidate_dataframe(
            frame=frame,
            key_columns=("KEY",),
            measure_columns=("MONTO_PIM",),
        )


def test_consolidate_dataframe_rejects_invalid_amounts() -> None:
    """Debe rechazar valores monetarios no numéricos."""
    frame = pd.DataFrame(
        [
            {
                "KEY": "A",
                "MONTO_PIM": "no-numérico",
            },
        ]
    )

    with pytest.raises(
        ValueError,
        match="valores no numéricos",
    ):
        consolidate_dataframe(
            frame=frame,
            key_columns=("KEY",),
            measure_columns=("MONTO_PIM",),
        )