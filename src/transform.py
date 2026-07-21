"""Transformación y consolidación de datos presupuestales del MEF."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pandas as pd

from src.analyze_grain import BUSINESS_KEY_V1


DEFAULT_RECONCILIATION_TOLERANCE = 0.01


def identify_measure_columns(
    columns: Sequence[str],
) -> list[str]:
    """Identifica las columnas monetarias del dataset."""
    return [
        str(column)
        for column in columns
        if str(column).startswith("MONTO_")
    ]


def validate_required_columns(
    columns: Sequence[str],
    required_columns: Sequence[str],
) -> None:
    """Comprueba que todas las columnas requeridas existan."""
    available_columns = {
        str(column)
        for column in columns
    }

    missing_columns = [
        column
        for column in required_columns
        if column not in available_columns
    ]

    if missing_columns:
        raise ValueError(
            "Faltan columnas requeridas para la transformación: "
            f"{missing_columns}"
        )


def normalize_string_columns(
    frame: pd.DataFrame,
    columns: Sequence[str],
) -> pd.DataFrame:
    """Recorta espacios y convierte cadenas vacías en valores nulos."""
    normalized = frame.copy()

    for column in columns:
        values = (
            normalized[column]
            .astype("string")
            .str.strip()
        )

        normalized[column] = values.mask(
            values.eq("")
        )

    return normalized


def convert_measure_columns(
    frame: pd.DataFrame,
    measure_columns: Sequence[str],
) -> pd.DataFrame:
    """Convierte las medidas a valores numéricos."""
    converted = frame.copy()

    for column in measure_columns:
        raw_values = (
            converted[column]
            .astype("string")
            .str.strip()
        )

        blank_mask = (
            raw_values.isna()
            | raw_values.eq("")
        )

        numeric_values = pd.to_numeric(
            raw_values.mask(blank_mask),
            errors="coerce",
        )

        parse_error_mask = (
            ~blank_mask
            & numeric_values.isna()
        )

        if parse_error_mask.any():
            error_count = int(
                parse_error_mask.sum()
            )

            raise ValueError(
                f"La columna '{column}' contiene "
                f"{error_count} valores no numéricos."
            )

        converted[column] = (
            numeric_values
            .fillna(0.0)
            .astype("float64")
        )

    return converted


def find_inconsistent_attributes(
    frame: pd.DataFrame,
    key_columns: Sequence[str],
    attribute_columns: Sequence[str],
) -> dict[str, int]:
    """Detecta atributos con más de un valor dentro de la clave."""
    if not attribute_columns:
        return {}

    grouped = frame.groupby(
        list(key_columns),
        dropna=False,
        sort=False,
    )

    inconsistencies: dict[str, int] = {}

    for column in attribute_columns:
        distinct_value_counts = grouped[
            column
        ].nunique(
            dropna=False,
        )

        inconsistent_group_count = int(
            distinct_value_counts.gt(1).sum()
        )

        if inconsistent_group_count > 0:
            inconsistencies[column] = (
                inconsistent_group_count
            )

    return inconsistencies


def calculate_measure_totals(
    frame: pd.DataFrame,
    measure_columns: Sequence[str],
) -> dict[str, float]:
    """Calcula los totales de las columnas monetarias."""
    return {
        column: float(frame[column].sum())
        for column in measure_columns
    }


def compare_measure_totals(
    totals_before: dict[str, float],
    totals_after: dict[str, float],
    tolerance: float,
) -> tuple[dict[str, float], bool]:
    """Compara los totales monetarios antes y después."""
    differences = {
        column: round(
            totals_after[column]
            - totals_before[column],
            10,
        )
        for column in totals_before
    }

    totals_preserved = all(
        abs(difference) <= tolerance
        for difference in differences.values()
    )

    return differences, totals_preserved


def consolidate_dataframe(
    frame: pd.DataFrame,
    key_columns: Sequence[str] = BUSINESS_KEY_V1,
    measure_columns: Sequence[str] | None = None,
    reconciliation_tolerance: float = (
        DEFAULT_RECONCILIATION_TOLERANCE
    ),
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Normaliza y consolida un DataFrame según la clave indicada."""
    if reconciliation_tolerance < 0:
        raise ValueError(
            "reconciliation_tolerance no puede ser negativo."
        )

    if measure_columns is None:
        measure_columns = identify_measure_columns(
            frame.columns
        )

    key_columns = tuple(key_columns)
    measure_columns = tuple(measure_columns)

    validate_required_columns(
        columns=frame.columns,
        required_columns=[
            *key_columns,
            *measure_columns,
        ],
    )

    non_measure_columns = [
        column
        for column in frame.columns
        if column not in measure_columns
    ]

    working = normalize_string_columns(
        frame=frame,
        columns=non_measure_columns,
    )

    working = convert_measure_columns(
        frame=working,
        measure_columns=measure_columns,
    )

    row_count_before = len(working)

    measure_totals_before = calculate_measure_totals(
        frame=working,
        measure_columns=measure_columns,
    )

    deduplicated = working.drop_duplicates(
        ignore_index=True,
    )

    exact_duplicate_rows_removed = (
        row_count_before
        - len(deduplicated)
    )

    attribute_columns = [
        column
        for column in deduplicated.columns
        if column not in key_columns
        and column not in measure_columns
    ]

    inconsistent_attributes = (
        find_inconsistent_attributes(
            frame=deduplicated,
            key_columns=key_columns,
            attribute_columns=attribute_columns,
        )
    )

    if inconsistent_attributes:
        raise ValueError(
            "Se detectaron atributos no monetarios "
            "inconsistentes dentro de la clave: "
            f"{inconsistent_attributes}"
        )

    aggregation_rules: dict[str, str] = {
        column: "first"
        for column in attribute_columns
    }

    aggregation_rules.update(
        {
            column: "sum"
            for column in measure_columns
        }
    )

    consolidated = (
        deduplicated
        .groupby(
            list(key_columns),
            dropna=False,
            sort=False,
            as_index=False,
        )
        .agg(aggregation_rules)
    )

    original_column_order = [
        column
        for column in frame.columns
        if column in consolidated.columns
    ]

    consolidated = consolidated[
        original_column_order
    ]

    measure_totals_after = calculate_measure_totals(
        frame=consolidated,
        measure_columns=measure_columns,
    )

    (
        measure_total_differences,
        totals_preserved,
    ) = compare_measure_totals(
        totals_before=measure_totals_before,
        totals_after=measure_totals_after,
        tolerance=reconciliation_tolerance,
    )

    if not totals_preserved:
        raise ValueError(
            "Los totales monetarios no se conservaron "
            "después de la consolidación: "
            f"{measure_total_differences}"
        )

    report = {
        "row_count_before": row_count_before,
        "row_count_after_exact_deduplication": len(
            deduplicated
        ),
        "row_count_after_consolidation": len(
            consolidated
        ),
        "exact_duplicate_rows_removed": (
            exact_duplicate_rows_removed
        ),
        "rows_consolidated": (
            len(deduplicated)
            - len(consolidated)
        ),
        "key_column_count": len(key_columns),
        "measure_column_count": len(
            measure_columns
        ),
        "attribute_column_count": len(
            attribute_columns
        ),
        "inconsistent_attributes": (
            inconsistent_attributes
        ),
        "measure_totals_before": (
            measure_totals_before
        ),
        "measure_totals_after": (
            measure_totals_after
        ),
        "measure_total_differences": (
            measure_total_differences
        ),
        "totals_preserved": totals_preserved,
        "reconciliation_tolerance": (
            reconciliation_tolerance
        ),
    }

    return consolidated, report