"""Detección por bloques de filas completamente duplicadas."""

from __future__ import annotations

import hashlib
from typing import Any

import pandas as pd


def normalize_value(value: Any) -> str:
    """Convierte un valor en una representación estable para hashing."""
    if pd.isna(value):
        return "<NULL>"

    return str(value)


def calculate_row_hash(row: pd.Series) -> str:
    """Calcula un hash SHA-256 estable a partir de una fila completa."""
    serialized_row = "\x1f".join(
        normalize_value(value)
        for value in row.tolist()
    )

    return hashlib.sha256(
        serialized_row.encode("utf-8")
    ).hexdigest()