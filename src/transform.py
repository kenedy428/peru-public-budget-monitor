"""Transformación y consolidación de datos presupuestales del MEF."""

from __future__ import annotations

import csv
import os
import sqlite3
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from src.analyze_grain import BUSINESS_KEY_V1
from src.check_duplicates import calculate_values_hash


DEFAULT_RECONCILIATION_TOLERANCE = 0.01
DEFAULT_FILE_CHUNK_ROWS = 50_000

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

def quote_identifier(identifier: str) -> str:
    """Protege un identificador para utilizarlo en SQLite."""
    return '"' + identifier.replace('"', '""') + '"'


def configure_file_transform_database(
    connection: sqlite3.Connection,
    columns: Sequence[str],
    measure_columns: Sequence[str],
) -> None:
    """Crea las tablas temporales para consolidar un archivo."""
    connection.execute("PRAGMA journal_mode = OFF")
    connection.execute("PRAGMA synchronous = OFF")
    connection.execute("PRAGMA temp_store = MEMORY")
    connection.execute("PRAGMA locking_mode = EXCLUSIVE")

    measure_set = set(measure_columns)

    column_definitions = ",\n".join(
        (
            f"{quote_identifier(column)} "
            f"{'REAL' if column in measure_set else 'TEXT'}"
        )
        for column in columns
    )

    connection.execute(
        """
        CREATE TABLE seen_row_hashes (
            row_hash TEXT PRIMARY KEY
        ) WITHOUT ROWID
        """
    )

    connection.execute(
        f"""
        CREATE TABLE incoming_rows (
            row_hash TEXT PRIMARY KEY,
            key_hash TEXT NOT NULL,
            first_row_number INTEGER NOT NULL,
            {column_definitions}
        ) WITHOUT ROWID
        """
    )

    connection.execute(
        f"""
        CREATE TABLE consolidated_rows (
            key_hash TEXT PRIMARY KEY,
            first_row_number INTEGER NOT NULL,
            occurrence_count INTEGER NOT NULL,
            inconsistent INTEGER NOT NULL,
            {column_definitions}
        ) WITHOUT ROWID
        """
    )


def build_incoming_insert_sql(
    columns: Sequence[str],
) -> str:
    """Construye la inserción de un lote normalizado."""
    insert_columns = [
        "row_hash",
        "key_hash",
        "first_row_number",
        *columns,
    ]

    quoted_columns = ", ".join(
        quote_identifier(column)
        for column in insert_columns
    )

    placeholders = ", ".join(
        "?"
        for _ in insert_columns
    )

    return (
        "INSERT OR IGNORE INTO incoming_rows "
        f"({quoted_columns}) "
        f"VALUES ({placeholders})"
    )


def build_consolidation_upsert_sql(
    columns: Sequence[str],
    measure_columns: Sequence[str],
) -> str:
    """Construye la consolidación incremental por clave."""
    measure_set = set(measure_columns)

    non_measure_columns = [
        column
        for column in columns
        if column not in measure_set
    ]

    mismatch_conditions = [
        (
            "NOT ("
            f"consolidated_rows.{quote_identifier(column)} "
            "IS "
            f"excluded.{quote_identifier(column)}"
            ")"
        )
        for column in non_measure_columns
    ]

    mismatch_expression = (
        " OR ".join(mismatch_conditions)
        if mismatch_conditions
        else "0"
    )

    update_clauses = [
        (
            "occurrence_count = "
            "consolidated_rows.occurrence_count + 1"
        ),
        (
            "inconsistent = CASE "
            "WHEN consolidated_rows.inconsistent = 1 "
            f"OR ({mismatch_expression}) "
            "THEN 1 ELSE 0 END"
        ),
    ]

    update_clauses.extend(
        (
            f"{quote_identifier(column)} = "
            "COALESCE("
            f"consolidated_rows.{quote_identifier(column)}, 0"
            ") + "
            "COALESCE("
            f"excluded.{quote_identifier(column)}, 0"
            ")"
        )
        for column in measure_columns
    )

    insert_columns = [
        "key_hash",
        "first_row_number",
        "occurrence_count",
        "inconsistent",
        *columns,
    ]

    quoted_insert_columns = ", ".join(
        quote_identifier(column)
        for column in insert_columns
    )

    selected_columns = ", ".join(
        [
            "key_hash",
            "first_row_number",
            "1",
            "0",
            *(
                quote_identifier(column)
                for column in columns
            ),
        ]
    )

    update_expression = ",\n".join(
        update_clauses
    )

    return f"""
        INSERT INTO consolidated_rows (
            {quoted_insert_columns}
        )
        SELECT
            {selected_columns}
        FROM incoming_rows
        WHERE 1
        ON CONFLICT(key_hash) DO UPDATE SET
            {update_expression}
    """


def transform_csv_file(
    source_file_path: Path,
    output_file_path: Path,
    encoding: str = "utf-8-sig",
    key_columns: Sequence[str] = BUSINESS_KEY_V1,
    chunk_rows: int = DEFAULT_FILE_CHUNK_ROWS,
    reconciliation_tolerance: float = (
        DEFAULT_RECONCILIATION_TOLERANCE
    ),
    temporary_directory: Path | None = None,
) -> dict[str, Any]:
    """Transforma y consolida globalmente un archivo CSV."""
    if chunk_rows <= 0:
        raise ValueError(
            "chunk_rows debe ser mayor que cero."
        )

    if reconciliation_tolerance < 0:
        raise ValueError(
            "reconciliation_tolerance no puede ser negativo."
        )

    source_file_path = Path(source_file_path)
    output_file_path = Path(output_file_path)

    if not source_file_path.exists():
        raise FileNotFoundError(
            f"No existe el archivo fuente: {source_file_path}"
        )

    header = (
        pd.read_csv(
            source_file_path,
            encoding=encoding,
            nrows=0,
        )
        .columns
        .astype(str)
        .tolist()
    )

    measure_columns = identify_measure_columns(
        header
    )

    validate_required_columns(
        columns=header,
        required_columns=[
            *key_columns,
            *measure_columns,
        ],
    )

    non_measure_columns = [
        column
        for column in header
        if column not in measure_columns
    ]

    output_file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_parent = (
        Path(temporary_directory)
        if temporary_directory is not None
        else output_file_path.parent
    )

    temporary_parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    descriptor, database_name = tempfile.mkstemp(
        prefix="transform_",
        suffix=".sqlite",
        dir=temporary_parent,
    )
    os.close(descriptor)

    database_path = Path(database_name)
    connection: sqlite3.Connection | None = None

    row_count_before = 0
    exact_duplicate_rows_removed = 0
    batch_count = 0

    measure_totals_before = {
        column: 0.0
        for column in measure_columns
    }

    try:
        connection = sqlite3.connect(
            database_path
        )

        configure_file_transform_database(
            connection=connection,
            columns=header,
            measure_columns=measure_columns,
        )

        incoming_insert_sql = (
            build_incoming_insert_sql(
                columns=header,
            )
        )

        consolidation_upsert_sql = (
            build_consolidation_upsert_sql(
                columns=header,
                measure_columns=measure_columns,
            )
        )

        column_indexes = {
            column: index
            for index, column in enumerate(header)
        }

        key_indexes = [
            column_indexes[column]
            for column in key_columns
        ]

        data_row_offset = 0

        chunks = pd.read_csv(
            source_file_path,
            encoding=encoding,
            dtype="string",
            keep_default_na=False,
            chunksize=chunk_rows,
            low_memory=False,
        )

        for chunk in chunks:
            working = normalize_string_columns(
                frame=chunk,
                columns=non_measure_columns,
            )

            working = convert_measure_columns(
                frame=working,
                measure_columns=measure_columns,
            )

            chunk_totals = calculate_measure_totals(
                frame=working,
                measure_columns=measure_columns,
            )

            for column, value in chunk_totals.items():
                measure_totals_before[column] += value

            staged_rows = []

            for local_offset, row_values in enumerate(
                working.itertuples(
                    index=False,
                    name=None,
                )
            ):
                database_values = tuple(
                    None
                    if pd.isna(value)
                    else value
                    for value in row_values
                )

                key_hash = calculate_values_hash(
                    database_values[index]
                    for index in key_indexes
                )

                row_hash = calculate_values_hash(
                    database_values
                )

                row_number = (
                    data_row_offset
                    + local_offset
                    + 2
                )

                staged_rows.append(
                    (
                        row_hash,
                        key_hash,
                        row_number,
                        *database_values,
                    )
                )

            connection.execute(
                "DELETE FROM incoming_rows"
            )

            connection.executemany(
                incoming_insert_sql,
                staged_rows,
            )

            connection.execute(
                """
                DELETE FROM incoming_rows
                WHERE row_hash IN (
                    SELECT row_hash
                    FROM seen_row_hashes
                )
                """
            )

            new_row_count = int(
                connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM incoming_rows
                    """
                ).fetchone()[0]
            )

            exact_duplicate_rows_removed += (
                len(working)
                - new_row_count
            )

            connection.execute(
                """
                INSERT OR IGNORE INTO seen_row_hashes (
                    row_hash
                )
                SELECT row_hash
                FROM incoming_rows
                """
            )

            connection.execute(
                consolidation_upsert_sql
            )

            connection.commit()

            row_count_before += len(working)
            data_row_offset += len(working)
            batch_count += 1

        inconsistent_group_count = int(
            connection.execute(
                """
                SELECT COUNT(*)
                FROM consolidated_rows
                WHERE inconsistent = 1
                """
            ).fetchone()[0]
        )

        if inconsistent_group_count > 0:
            raise ValueError(
                "Se detectaron "
                f"{inconsistent_group_count} claves "
                "con atributos no monetarios inconsistentes."
            )

        row_count_after_consolidation = int(
            connection.execute(
                """
                SELECT COUNT(*)
                FROM consolidated_rows
                """
            ).fetchone()[0]
        )

        measure_sum_expression = ", ".join(
            (
                "SUM("
                f"{quote_identifier(column)}"
                ")"
            )
            for column in measure_columns
        )

        measure_sum_row = connection.execute(
            f"""
            SELECT {measure_sum_expression}
            FROM consolidated_rows
            """
        ).fetchone()

        measure_totals_after = {
            column: float(
                measure_sum_row[index] or 0.0
            )
            for index, column in enumerate(
                measure_columns
            )
        }

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

        output_column_expression = ", ".join(
            quote_identifier(column)
            for column in header
        )

        cursor = connection.execute(
            f"""
            SELECT {output_column_expression}
            FROM consolidated_rows
            ORDER BY first_row_number
            """
        )

        with output_file_path.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as output_file:
            writer = csv.writer(output_file)
            writer.writerow(header)

            while True:
                rows = cursor.fetchmany(10_000)

                if not rows:
                    break

                writer.writerows(rows)

        unique_full_row_count = (
            row_count_before
            - exact_duplicate_rows_removed
        )

        return {
            "row_count_before": row_count_before,
            "exact_duplicate_rows_removed": (
                exact_duplicate_rows_removed
            ),
            "unique_full_row_count": (
                unique_full_row_count
            ),
            "row_count_after_consolidation": (
                row_count_after_consolidation
            ),
            "rows_consolidated": (
                unique_full_row_count
                - row_count_after_consolidation
            ),
            "total_rows_removed": (
                row_count_before
                - row_count_after_consolidation
            ),
            "batch_count": batch_count,
            "key_column_count": len(key_columns),
            "measure_column_count": len(
                measure_columns
            ),
            "inconsistent_group_count": (
                inconsistent_group_count
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
            "output_file_path": str(
                output_file_path
            ),
        }

    finally:
        if connection is not None:
            connection.close()

        database_path.unlink(
            missing_ok=True
        )