"""Pruebas unitarias para la detección de duplicados."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.check_duplicates import (
    calculate_row_hash,
    normalize_value,
    scan_duplicate_rows,
)


def test_normalize_value_handles_nulls() -> None:
    """Los nulos deben tener una representación estable."""
    assert normalize_value(None) == "<NULL>"
    assert normalize_value(float("nan")) == "<NULL>"


def test_calculate_row_hash_is_stable() -> None:
    """La misma fila debe producir siempre el mismo hash."""
    row = pd.Series([2026, "NACIONAL", 100.5])

    first_hash = calculate_row_hash(row)
    second_hash = calculate_row_hash(row)

    assert first_hash == second_hash
    assert len(first_hash) == 64


def test_calculate_row_hash_distinguishes_rows() -> None:
    """Filas diferentes deben producir hashes diferentes."""
    first_row = pd.Series([2026, "NACIONAL", 100.5])
    second_row = pd.Series([2026, "REGIONAL", 100.5])

    assert (
        calculate_row_hash(first_row)
        != calculate_row_hash(second_row)
    )


def test_scan_duplicate_rows_detects_duplicates_across_batches(
    tmp_path: Path,
) -> None:
    """Debe detectar duplicados ubicados en lotes diferentes."""
    raw_dir = tmp_path / "raw"
    quality_dir = tmp_path / "quality"
    raw_dir.mkdir()

    file_path = raw_dir / "sample.csv"
    file_path.write_text(
        (
            "ID,NOMBRE\n"
            "1,ALFA\n"
            "2,BETA\n"
            "3,GAMMA\n"
            "1,ALFA\n"
            "2,BETA\n"
        ),
        encoding="utf-8",
    )

    source = {
        "source_id": "test_source",
        "resource_name": "sample.csv",
        "reference_year": 2026,
        "encoding": "utf-8",
    }

    result = scan_duplicate_rows(
        source=source,
        raw_data_dir=raw_dir,
        quality_dir=quality_dir,
        batch_rows=2,
    )

    assert result["row_count"] == 5
    assert result["unique_row_count"] == 3
    assert result["duplicate_group_count"] == 2
    assert result["duplicate_row_count"] == 2
    assert result["rows_in_duplicate_groups"] == 4
    assert result["maximum_occurrence_count"] == 2
    assert result["duplicate_control"]["status"] == "warning"


def test_scan_duplicate_rows_accepts_unique_rows(
    tmp_path: Path,
) -> None:
    """Un archivo sin repeticiones debe aprobar el control."""
    raw_dir = tmp_path / "raw"
    quality_dir = tmp_path / "quality"
    raw_dir.mkdir()

    file_path = raw_dir / "sample.csv"
    file_path.write_text(
        (
            "ID,NOMBRE\n"
            "1,ALFA\n"
            "2,BETA\n"
            "3,GAMMA\n"
        ),
        encoding="utf-8",
    )

    source = {
        "source_id": "test_source",
        "resource_name": "sample.csv",
        "reference_year": 2026,
        "encoding": "utf-8",
    }

    result = scan_duplicate_rows(
        source=source,
        raw_data_dir=raw_dir,
        quality_dir=quality_dir,
        batch_rows=2,
    )

    assert result["row_count"] == 3
    assert result["unique_row_count"] == 3
    assert result["duplicate_group_count"] == 0
    assert result["duplicate_row_count"] == 0
    assert result["duplicate_control"]["status"] == "passed"