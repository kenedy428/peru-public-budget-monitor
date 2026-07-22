"""Pruebas de transformación y consolidación."""

from __future__ import annotations

import pandas as pd
import pytest
import json
from pathlib import Path
from src.transform import (
    consolidate_dataframe,
    identify_measure_columns,
    transform_source,
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

def test_transform_csv_file_consolidates_across_chunks(
    tmp_path,
) -> None:
    """Debe consolidar y deduplicar entre bloques diferentes."""
    from pathlib import Path

    from src.transform import transform_csv_file

    source_path = Path(tmp_path) / "source.csv"
    output_path = Path(tmp_path) / "processed.csv"

    source_path.write_text(
        (
            "KEY,DESCRIPTION,"
            "MONTO_PIM,MONTO_CERTIFICADO_ANUAL\n"
            "C,Registro cero,0,0\n"
            "A,Registro A,100,0\n"
            "B,Registro B,50,25\n"
            "A,Registro A,0,80\n"
            "C,Registro cero,0,0\n"
        ),
        encoding="utf-8",
    )

    report = transform_csv_file(
        source_file_path=source_path,
        output_file_path=output_path,
        encoding="utf-8",
        key_columns=("KEY",),
        chunk_rows=2,
    )

    processed = pd.read_csv(
        output_path,
        encoding="utf-8",
    )

    assert report["row_count_before"] == 5
    assert report["exact_duplicate_rows_removed"] == 1
    assert report["unique_full_row_count"] == 4
    assert report["row_count_after_consolidation"] == 3
    assert report["rows_consolidated"] == 1
    assert report["total_rows_removed"] == 2
    assert report["batch_count"] == 3
    assert report["totals_preserved"] is True

    assert len(processed) == 3

    consolidated_a = processed.loc[
        processed["KEY"].eq("A")
    ].iloc[0]

    assert consolidated_a["MONTO_PIM"] == 100
    assert (
        consolidated_a["MONTO_CERTIFICADO_ANUAL"]
        == 80
    )

def test_transform_source_writes_output_and_report(
    tmp_path: Path,
) -> None:
    """Debe generar el CSV consolidado y su reporte JSON."""
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"

    raw_dir.mkdir()

    source_path = raw_dir / "sample.csv"

    source_path.write_text(
        (
            "KEY,DESCRIPTION,"
            "MONTO_PIM,MONTO_CERTIFICADO_ANUAL\n"
            "A,Registro A,100,0\n"
            "A,Registro A,0,80\n"
        ),
        encoding="utf-8",
    )

    source = {
        "source_id": "test_source",
        "resource_name": "sample.csv",
        "reference_year": 2026,
        "encoding": "utf-8",
    }

    report, report_path = transform_source(
        source=source,
        raw_data_dir=raw_dir,
        processed_dir=processed_dir,
        chunk_rows=1,
        reconciliation_tolerance=0.01,
        key_columns=("KEY",),
    )

    output_path = Path(
        report["output_file_path"]
    )

    assert output_path.exists()
    assert report_path.exists()

    assert report["source_id"] == "test_source"
    assert report["reference_year"] == 2026
    assert report["row_count_before"] == 2
    assert (
        report["row_count_after_consolidation"]
        == 1
    )
    assert report["rows_consolidated"] == 1
    assert report["totals_preserved"] is True

    stored_report = json.loads(
        report_path.read_text(
            encoding="utf-8"
        )
    )

    assert stored_report["source_id"] == "test_source"
    assert stored_report["totals_preserved"] is True

    processed = pd.read_csv(
        output_path,
        encoding="utf-8",
    )

    assert len(processed) == 1
    assert processed.iloc[0]["MONTO_PIM"] == 100
    assert (
        processed.iloc[0][
            "MONTO_CERTIFICADO_ANUAL"
        ]
        == 80
    )