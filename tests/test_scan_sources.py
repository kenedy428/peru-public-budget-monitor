"""Pruebas unitarias para el escaneo de contenido."""

from __future__ import annotations

from pathlib import Path

from src.scan_sources import scan_csv_content


def test_scan_csv_content_counts_rows_and_months(
    tmp_path: Path,
) -> None:
    """Debe contar filas y detectar el último mes poblado."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    file_path = raw_dir / "sample.csv"
    file_path.write_text(
        (
            "ANO_EJE,MONTO_DEVENGADO_ENERO,"
            "MONTO_DEVENGADO_FEBRERO,"
            "MONTO_DEVENGADO_MARZO,"
            "MONTO_DEVENGADO_ANUAL\n"
            "2026,10,0,0,10\n"
            "2026,0,0,5,5\n"
            "2026,,0,0,0\n"
        ),
        encoding="utf-8",
    )

    source = {
        "source_id": "test_source",
        "resource_name": "sample.csv",
        "reference_year": 2026,
        "encoding": "utf-8",
    }

    result = scan_csv_content(
        source=source,
        raw_data_dir=raw_dir,
        chunk_rows=2,
    )

    assert result["row_count"] == 3
    assert result["chunk_count"] == 2
    assert result["last_populated_month"] == "MARZO"

    january = result["monthly_stats"][
        "MONTO_DEVENGADO_ENERO"
    ]

    assert january["non_null_count"] == 2
    assert january["null_count"] == 1
    assert january["non_zero_count"] == 1


def test_scan_csv_content_returns_none_when_all_months_are_zero(
    tmp_path: Path,
) -> None:
    """Sin montos distintos de cero no debe existir último mes."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    file_path = raw_dir / "sample.csv"
    file_path.write_text(
        (
            "MONTO_DEVENGADO_ENERO,"
            "MONTO_DEVENGADO_FEBRERO,"
            "MONTO_DEVENGADO_ANUAL\n"
            "0,0,0\n"
            "0,0,0\n"
        ),
        encoding="utf-8",
    )

    source = {
        "source_id": "test_source",
        "resource_name": "sample.csv",
        "encoding": "utf-8",
    }

    result = scan_csv_content(
        source=source,
        raw_data_dir=raw_dir,
        chunk_rows=1,
    )

    assert result["row_count"] == 2
    assert result["last_populated_month"] is None
    assert result["populated_month_columns"] == []