"""Pruebas del análisis del grano y claves candidatas."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.analyze_grain import analyze_candidate_keys


def test_analyze_candidate_keys_detects_compact_collisions(
    tmp_path: Path,
) -> None:
    """Una clave reducida debe detectar colisiones adicionales."""
    raw_dir = tmp_path / "raw"
    profiling_dir = tmp_path / "profiling"
    raw_dir.mkdir()

    file_path = raw_dir / "sample.csv"
    file_path.write_text(
        (
            "A,B,C,MONTO\n"
            "1,X,P,10\n"
            "1,X,Q,20\n"
            "2,Y,P,30\n"
        ),
        encoding="utf-8",
    )

    source = {
        "source_id": "test_source",
        "resource_name": "sample.csv",
        "reference_year": 2026,
        "encoding": "utf-8",
    }

    candidate_keys = {
        "maximal": (
            "A",
            "B",
            "C",
        ),
        "compact": (
            "A",
            "B",
        ),
    }

    report = analyze_candidate_keys(
        source=source,
        raw_data_dir=raw_dir,
        profiling_dir=profiling_dir,
        batch_rows=2,
        candidate_keys=candidate_keys,
    )

    maximal = report["candidate_keys"]["maximal"]
    compact = report["candidate_keys"]["compact"]

    assert report["analyzed_row_count"] == 3

    assert maximal["unique_key_count"] == 3
    assert maximal["duplicate_group_count"] == 0
    assert maximal["duplicate_key_row_count"] == 0

    assert compact["unique_key_count"] == 2
    assert compact["duplicate_group_count"] == 1
    assert compact["duplicate_key_row_count"] == 1
    assert compact["maximum_occurrence_count"] == 2


def test_analyze_candidate_keys_rejects_missing_columns(
    tmp_path: Path,
) -> None:
    """Debe rechazar una clave que use columnas inexistentes."""
    raw_dir = tmp_path / "raw"
    profiling_dir = tmp_path / "profiling"
    raw_dir.mkdir()

    file_path = raw_dir / "sample.csv"
    file_path.write_text(
        "A,B\n1,2\n",
        encoding="utf-8",
    )

    source = {
        "source_id": "test_source",
        "resource_name": "sample.csv",
        "reference_year": 2026,
        "encoding": "utf-8",
    }

    with pytest.raises(
        ValueError,
        match="columnas inexistentes",
    ):
        analyze_candidate_keys(
            source=source,
            raw_data_dir=raw_dir,
            profiling_dir=profiling_dir,
            batch_rows=2,
            candidate_keys={
                "invalid": (
                    "A",
                    "C",
                ),
            },
        )