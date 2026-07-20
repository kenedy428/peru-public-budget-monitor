"""Pruebas unitarias para la detección de duplicados."""

from __future__ import annotations

import pandas as pd

from src.check_duplicates import (
    calculate_row_hash,
    normalize_value,
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