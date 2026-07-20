"""Validación por bloques de la calidad de las fuentes oficiales del MEF."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.extract import (
    DEFAULT_CONFIG_PATH,
    PROJECT_ROOT,
    load_config,
)
from src.profile_sources import (
    classify_devengado_columns,
    select_sources,
)


DEFAULT_CHUNK_ROWS = 100_000
DEFAULT_RECONCILIATION_TOLERANCE = 0.01


def configure_logging() -> None:
    """Configura los mensajes mostrados en consola."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def get_report_path(file_path: Path) -> str:
    """Obtiene una ruta portable para incluirla en el reporte."""
    try:
        return file_path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return file_path.as_posix()


def determine_reconciliation_status(
    mismatch_count: int,
    not_evaluated_count: int,
) -> str:
    """Clasifica el resultado de la reconciliación anual."""
    if mismatch_count > 0:
        return "failed"

    if not_evaluated_count > 0:
        return "warning"

    return "passed"

def identify_monetary_columns(
    columns: list[str],
) -> list[str]:
    """Identifica las columnas que representan montos monetarios."""
    return [
        column
        for column in columns
        if column.upper().startswith("MONTO_")
    ]

def validate_source_quality(
    source: dict[str, Any],
    raw_data_dir: Path,
    chunk_rows: int,
    reconciliation_tolerance: float,
) -> dict[str, Any]:
    """Evalúa controles básicos de calidad procesando el CSV por bloques."""
    if chunk_rows <= 0:
        raise ValueError("chunk_rows debe ser mayor que cero.")

    if reconciliation_tolerance < 0:
        raise ValueError(
            "reconciliation_tolerance no puede ser negativo."
        )

    source_id = source["source_id"]
    resource_name = source["resource_name"]
    reference_year = source.get("reference_year")
    encoding = source.get("encoding", "utf-8-sig")
    file_path = raw_data_dir / resource_name

    if reference_year is None:
        raise ValueError(
            f"La fuente '{source_id}' no tiene un año de referencia."
        )

    if not file_path.exists():
        raise FileNotFoundError(
            f"No existe el archivo local para '{source_id}': {file_path}"
        )

    header = pd.read_csv(
        file_path,
        encoding=encoding,
        nrows=0,
    )
    columns = header.columns.astype(str).tolist()
    monetary_columns = identify_monetary_columns(columns)

    if not monetary_columns:
        raise ValueError(
            f"La fuente '{source_id}' no contiene columnas monetarias."
        )
    (
        monthly_columns,
        annual_columns,
        _other_devengado_columns,
    ) = classify_devengado_columns(columns)

    required_columns = ["ANO_EJE"]

    if len(monthly_columns) != 12:
        raise ValueError(
            f"La fuente '{source_id}' debe contener las doce "
            "columnas mensuales de Devengado."
        )

    if len(annual_columns) != 1:
        raise ValueError(
            f"La fuente '{source_id}' debe contener exactamente "
            "una columna anual de Devengado."
        )

    required_columns.extend(monthly_columns)
    required_columns.extend(annual_columns)

    missing_required_columns = [
        column
        for column in required_columns
        if column not in columns
    ]

    if missing_required_columns:
        raise ValueError(
            "Faltan columnas requeridas: "
            + ", ".join(missing_required_columns)
        )

    annual_column = annual_columns[0]
    amount_columns = monetary_columns

    null_counts = {
        column: 0
        for column in columns
    }
    amount_parse_error_counts = {
        column: 0
        for column in amount_columns
    }
    negative_amount_counts = {
    column: 0
    for column in amount_columns
    }
    row_count = 0
    chunk_count = 0

    year_null_count = 0
    year_parse_error_count = 0
    year_mismatch_count = 0
    observed_years: set[int | float] = set()

    reconciliation_evaluated_count = 0
    reconciliation_match_count = 0
    reconciliation_mismatch_count = 0
    reconciliation_not_evaluated_count = 0
    maximum_absolute_difference = 0.0

    logging.info(
        "Validando %s en bloques de %s filas.",
        resource_name,
        chunk_rows,
    )

    chunks = pd.read_csv(
        file_path,
        encoding=encoding,
        chunksize=chunk_rows,
        low_memory=False,
    )

    for chunk in chunks:
        chunk_count += 1
        row_count += len(chunk)

        chunk_null_counts = chunk.isna().sum()

        for column, value in chunk_null_counts.items():
            null_counts[str(column)] += int(value)

        raw_year_values = chunk["ANO_EJE"]
        numeric_year_values = pd.to_numeric(
            raw_year_values,
            errors="coerce",
        )

        year_null_count += int(
            raw_year_values.isna().sum()
        )
        year_parse_error_count += int(
            (
                raw_year_values.notna()
                & numeric_year_values.isna()
            ).sum()
        )
        year_mismatch_count += int(
            (
                numeric_year_values.notna()
                & numeric_year_values.ne(reference_year)
            ).sum()
        )

        for value in numeric_year_values.dropna().unique():
            numeric_value = float(value)

            if numeric_value.is_integer():
                observed_years.add(int(numeric_value))
            else:
                observed_years.add(numeric_value)

        numeric_amount_values = chunk[
            amount_columns
        ].apply(
            pd.to_numeric,
            errors="coerce",
        )

        numeric_monthly_values = numeric_amount_values[
            monthly_columns
        ]
        numeric_annual_values = numeric_amount_values[
            annual_column
        ]
        raw_annual_values = chunk[annual_column]

        for column in amount_columns:
            amount_parse_error_counts[column] += int(
                (
                    chunk[column].notna()
                    & numeric_amount_values[column].isna()
                ).sum()
            )

            negative_amount_counts[column] += int(
                numeric_amount_values[column].lt(0).sum()
            )

        comparable_mask = (
            numeric_monthly_values.notna().all(axis=1)
            & numeric_annual_values.notna()
        )

        monthly_sum = numeric_monthly_values.sum(
            axis=1,
            min_count=len(monthly_columns),
        )

        absolute_difference = (
            numeric_annual_values - monthly_sum
        ).abs()

        evaluated_differences = absolute_difference[
            comparable_mask
        ]

        match_mask = (
            evaluated_differences
            <= reconciliation_tolerance
        )
        mismatch_mask = (
            evaluated_differences
            > reconciliation_tolerance
        )

        reconciliation_evaluated_count += int(
            comparable_mask.sum()
        )
        reconciliation_match_count += int(
            match_mask.sum()
        )
        reconciliation_mismatch_count += int(
            mismatch_mask.sum()
        )
        reconciliation_not_evaluated_count += int(
            (~comparable_mask).sum()
        )

        if not evaluated_differences.empty:
            chunk_maximum_difference = float(
                evaluated_differences.max()
            )
            maximum_absolute_difference = max(
                maximum_absolute_difference,
                chunk_maximum_difference,
            )

        if chunk_count % 10 == 0:
            logging.info(
                "%s | bloques=%s | filas procesadas=%s",
                source_id,
                chunk_count,
                f"{row_count:,}",
            )

    null_rates = {
        column: (
            round(count / row_count, 8)
            if row_count > 0
            else None
        )
        for column, count in null_counts.items()
    }

    columns_with_nulls = [
        column
        for column, count in null_counts.items()
        if count > 0
    ]

    columns_with_negative_amounts = [
        column
        for column, count in negative_amount_counts.items()
        if count > 0
    ]

    total_negative_amount_count = sum(
        negative_amount_counts.values()
    )

    negative_amount_status = (
        "warning"
        if total_negative_amount_count > 0
        else "passed"
    )

    year_control_passed = (
        year_null_count == 0
        and year_parse_error_count == 0
        and year_mismatch_count == 0
    )

    reconciliation_status = determine_reconciliation_status(
        mismatch_count=reconciliation_mismatch_count,
        not_evaluated_count=reconciliation_not_evaluated_count,
    )

    return {
        "source_id": source_id,
        "resource_name": resource_name,
        "reference_year": reference_year,
        "local_path": get_report_path(file_path),
        "file_size_bytes": file_path.stat().st_size,
        "configured_encoding": encoding,
        "chunk_rows": chunk_rows,
        "chunk_count": chunk_count,
        "row_count": row_count,
        "column_count": len(columns),
        "columns": columns,
        "null_counts": null_counts,
        "null_rates": null_rates,
        "columns_with_nulls": columns_with_nulls,
        "columns_with_nulls_count": len(columns_with_nulls),
        "amount_parse_error_counts": amount_parse_error_counts,
        "negative_amounts": {
            "severity": "warning",
            "status": negative_amount_status,
            "columns_checked": monetary_columns,
            "column_count": len(monetary_columns),
            "negative_counts": negative_amount_counts,
            "columns_with_negative_amounts": (
                columns_with_negative_amounts
            ),
            "columns_with_negative_amounts_count": len(
                columns_with_negative_amounts
            ),
            "total_negative_amount_count": (
                total_negative_amount_count
            ),
            "rule": (
                "Los montos negativos se registran como advertencia "
                "y requieren revisión contextual."
            ),
        },
        "year_validation": {
            "severity": "critical",
            "status": (
                "passed"
                if year_control_passed
                else "failed"
            ),
            "expected_year": reference_year,
            "observed_years": sorted(
                observed_years,
                key=str,
            ),
            "null_count": year_null_count,
            "parse_error_count": year_parse_error_count,
            "mismatch_count": year_mismatch_count,
        },
        "annual_reconciliation": {
            "severity": "critical",
            "status": reconciliation_status,
            "annual_column": annual_column,
            "monthly_columns": monthly_columns,
            "tolerance": reconciliation_tolerance,
            "evaluated_count": reconciliation_evaluated_count,
            "match_count": reconciliation_match_count,
            "mismatch_count": reconciliation_mismatch_count,
            "not_evaluated_count": (
                reconciliation_not_evaluated_count
            ),
            "maximum_absolute_difference": round(
                maximum_absolute_difference,
                6,
            ),
            "rule": (
                "El monto anual debe coincidir con la suma de los "
                "doce montos mensuales dentro de la tolerancia."
            ),
        },
        "quality_summary": {
            "critical_controls_failed": sum(
                [
                    not year_control_passed,
                    reconciliation_status == "failed",
                ]
            ),
            "critical_controls_passed": sum(
                [
                    year_control_passed,
                    reconciliation_status == "passed",
                ]
            ),
            "warnings": sum(
                [
                    reconciliation_status == "warning",
                    len(columns_with_nulls) > 0,
                    any(
                        count > 0
                        for count in amount_parse_error_counts.values()
                    ),
                    negative_amount_status == "warning",
                ]
            ),
        },
        "validated_at_utc": datetime.now(UTC).isoformat(),
        "quality_version": "0.1.0",
    }


def write_quality_report(
    report: dict[str, Any],
    quality_dir: Path,
) -> Path:
    """Guarda el reporte de calidad en formato JSON."""
    quality_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    source_id = report["source_id"]

    report_path = (
        quality_dir
        / f"{timestamp}_{source_id}_quality.json"
    )

    with report_path.open("w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return report_path


def parse_arguments() -> argparse.Namespace:
    """Define los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description=(
            "Evalúa controles básicos de calidad sobre las "
            "fuentes oficiales del MEF mediante bloques."
        )
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Ruta del archivo YAML de configuración.",
    )
    parser.add_argument(
        "--source-id",
        help="Identificador de una fuente de datos.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Valida los recursos 2024, 2025 y 2026.",
    )
    parser.add_argument(
        "--chunk-rows",
        type=int,
        default=DEFAULT_CHUNK_ROWS,
        help="Cantidad de filas procesadas en cada bloque.",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=DEFAULT_RECONCILIATION_TOLERANCE,
        help=(
            "Diferencia máxima aceptada entre el monto anual "
            "y la suma mensual."
        ),
    )

    return parser.parse_args()


def main() -> int:
    """Punto de entrada de la validación de calidad."""
    configure_logging()
    args = parse_arguments()

    try:
        config = load_config(args.config)

        raw_data_dir = (
            PROJECT_ROOT
            / config["project"]["raw_data_dir"]
        )
        quality_dir = (
            PROJECT_ROOT
            / "data"
            / "quality"
        )

        sources = select_sources(
            config=config,
            source_id=args.source_id,
            profile_all=args.all,
        )

        for source in sources:
            report = validate_source_quality(
                source=source,
                raw_data_dir=raw_data_dir,
                chunk_rows=args.chunk_rows,
                reconciliation_tolerance=args.tolerance,
            )

            report_path = write_quality_report(
                report=report,
                quality_dir=quality_dir,
            )

            logging.info(
                "%s | filas=%s | año=%s | "
                "reconciliación=%s | nulos=%s",
                report["source_id"],
                f"{report['row_count']:,}",
                report["year_validation"]["status"],
                report["annual_reconciliation"]["status"],
                report["columns_with_nulls_count"],
            )
            logging.info(
                "Reporte generado: %s",
                report_path,
            )

        logging.info(
            "Validación de calidad finalizada correctamente."
        )
        return 0

    except Exception as error:
        logging.exception(
            "La validación de calidad falló: %s",
            error,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())