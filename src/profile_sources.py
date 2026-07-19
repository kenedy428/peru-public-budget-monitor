"""Perfilado estructural ligero de las fuentes oficiales del MEF."""

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


DEFAULT_SAMPLE_ROWS = 1_000
MONTH_NAMES = (
    "ENERO",
    "FEBRERO",
    "MARZO",
    "ABRIL",
    "MAYO",
    "JUNIO",
    "JULIO",
    "AGOSTO",
    "SEPTIEMBRE",
    "OCTUBRE",
    "NOVIEMBRE",
    "DICIEMBRE",
)

def configure_logging() -> None:
    """Configura los mensajes mostrados en consola."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def load_dictionary_variables(
    dictionary_path: Path,
    encoding: str,
) -> set[str]:
    """Obtiene las variables documentadas en el diccionario oficial."""
    if not dictionary_path.exists():
        raise FileNotFoundError(
            f"No existe el diccionario local: {dictionary_path}"
        )

    dictionary = pd.read_csv(
        dictionary_path,
        encoding=encoding,
        usecols=["VARIABLE"],
    )

    variables = (
        dictionary["VARIABLE"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    return set(variables)

def classify_devengado_columns(
    columns: list[str],
) -> tuple[list[str], list[str], list[str]]:
    """Clasifica columnas mensuales, anuales y adicionales de Devengado."""
    expected_monthly_columns = [
        f"MONTO_DEVENGADO_{month}"
        for month in MONTH_NAMES
    ]

    monthly_columns = [
        column
        for column in expected_monthly_columns
        if column in columns
    ]

    annual_columns = [
        column
        for column in columns
        if column == "MONTO_DEVENGADO_ANUAL"
    ]

    classified_columns = set(
        monthly_columns + annual_columns
    )

    other_devengado_columns = [
        column
        for column in columns
        if "DEVENGADO" in column.upper()
        and column not in classified_columns
    ]

    return (
        monthly_columns,
        annual_columns,
        other_devengado_columns,
    )


def compare_schemas(
    reports: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compara nombres, cantidad y orden de columnas entre fuentes."""
    if not reports:
        raise ValueError(
            "Se requiere al menos un reporte para comparar esquemas."
        )

    base_report = reports[0]
    base_source_id = base_report["source_id"]
    base_columns = base_report["columns"]
    base_column_set = set(base_columns)

    comparisons = []

    for report in reports:
        columns = report["columns"]
        column_set = set(columns)

        missing_columns = [
            column
            for column in base_columns
            if column not in column_set
        ]

        additional_columns = [
            column
            for column in columns
            if column not in base_column_set
        ]

        comparisons.append(
            {
                "source_id": report["source_id"],
                "column_count": len(columns),
                "same_column_count_as_base": (
                    len(columns) == len(base_columns)
                ),
                "same_column_names_as_base": (
                    column_set == base_column_set
                ),
                "same_column_order_as_base": (
                    columns == base_columns
                ),
                "missing_columns_vs_base": missing_columns,
                "additional_columns_vs_base": additional_columns,
            }
        )

    return {
        "base_source_id": base_source_id,
        "source_count": len(reports),
        "all_same_column_count": all(
            item["same_column_count_as_base"]
            for item in comparisons
        ),
        "all_same_column_names": all(
            item["same_column_names_as_base"]
            for item in comparisons
        ),
        "all_same_column_order": all(
            item["same_column_order_as_base"]
            for item in comparisons
        ),
        "comparisons": comparisons,
        "compared_at_utc": datetime.now(UTC).isoformat(),
        "profiling_version": "0.1.0",
    }


def write_schema_comparison_report(
    comparison: dict[str, Any],
    profiling_dir: Path,
) -> Path:
    """Guarda la comparación consolidada de esquemas."""
    profiling_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )

    report_path = (
        profiling_dir
        / f"{timestamp}_schema_comparison.json"
    )

    with report_path.open("w", encoding="utf-8") as file:
        json.dump(
            comparison,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return report_path

def profile_csv(
    source: dict[str, Any],
    raw_data_dir: Path,
    dictionary_variables: set[str],
    sample_rows: int,
) -> dict[str, Any]:
    """Perfila la cabecera y una muestra limitada de un archivo CSV."""
    source_id = source["source_id"]
    resource_name = source["resource_name"]
    encoding = source.get("encoding", "utf-8-sig")
    file_path = raw_data_dir / resource_name

    if not file_path.exists():
        raise FileNotFoundError(
            f"No existe el archivo local para '{source_id}': {file_path}"
        )

    logging.info(
        "Perfilando %s con una muestra máxima de %s filas.",
        resource_name,
        sample_rows,
    )

    header = pd.read_csv(
        file_path,
        encoding=encoding,
        nrows=0,
    )
    columns = header.columns.astype(str).tolist()

    sample = pd.read_csv(
        file_path,
        encoding=encoding,
        nrows=sample_rows,
        low_memory=False,
    )

    inferred_dtypes = {
        column: str(dtype)
        for column, dtype in sample.dtypes.items()
    }

    sample_null_counts = {
        column: int(value)
        for column, value in sample.isna().sum().items()
    }

    documented_columns = [
        column
        for column in columns
        if column in dictionary_variables
    ]
    undocumented_columns = [
        column
        for column in columns
        if column not in dictionary_variables
    ]
    dictionary_only_columns = sorted(
        dictionary_variables.difference(columns)
    )

    devengado_columns = [
        column
        for column in columns
        if "DEVENGADO" in column.upper()
    ]
    (
        monthly_devengado_columns,
        annual_devengado_columns,
        other_devengado_columns,
    ) = classify_devengado_columns(columns)

    return {
        "source_id": source_id,
        "resource_name": resource_name,
        "reference_year": source.get("reference_year"),
        "local_path": file_path.relative_to(PROJECT_ROOT).as_posix(),
        "file_size_bytes": file_path.stat().st_size,
        "configured_encoding": encoding,
        "sample_rows_requested": sample_rows,
        "sample_rows_read": int(len(sample)),
        "column_count": len(columns),
        "columns": columns,
        "inferred_dtypes_from_sample": inferred_dtypes,
        "sample_null_counts": sample_null_counts,
        "documented_column_count": len(documented_columns),
        "documented_columns": documented_columns,
        "undocumented_column_count": len(undocumented_columns),
        "undocumented_columns": undocumented_columns,
        "dictionary_only_column_count": len(dictionary_only_columns),
        "dictionary_only_columns": dictionary_only_columns,
        "devengado_column_count": len(devengado_columns),
        "devengado_columns": devengado_columns,
        "monthly_devengado_column_count": len(monthly_devengado_columns),
        "monthly_devengado_columns": monthly_devengado_columns,
        "annual_devengado_column_count": len(annual_devengado_columns),
        "annual_devengado_columns": annual_devengado_columns,
        "other_devengado_column_count": len(other_devengado_columns),
        "other_devengado_columns": other_devengado_columns,
        "profiled_at_utc": datetime.now(UTC).isoformat(),
        "profiling_version": "0.1.0",
    }


def write_report(
    report: dict[str, Any],
    profiling_dir: Path,
) -> Path:
    """Guarda el resultado del perfilado en formato JSON."""
    profiling_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    source_id = report["source_id"]

    report_path = (
        profiling_dir
        / f"{timestamp}_{source_id}_profile.json"
    )

    with report_path.open("w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return report_path


def select_sources(
    config: dict[str, Any],
    source_id: str | None,
    profile_all: bool,
) -> list[dict[str, Any]]:
    """Selecciona las fuentes de datos que serán perfiladas."""
    data_sources = [
        source
        for source in config["sources"]
        if source.get("resource_type") == "data"
    ]

    if profile_all:
        return data_sources

    selected_id = source_id or "mef_devengado_2026"

    selected = [
        source
        for source in data_sources
        if source["source_id"] == selected_id
    ]

    if not selected:
        available = ", ".join(
            source["source_id"]
            for source in data_sources
        )
        raise ValueError(
            f"No existe la fuente de datos '{selected_id}'. "
            f"Fuentes disponibles: {available}"
        )

    return selected


def parse_arguments() -> argparse.Namespace:
    """Define los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description=(
            "Perfila cabeceras y muestras de las fuentes del MEF "
            "sin cargar los archivos completos en memoria."
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
        help="Perfila los recursos 2024, 2025 y 2026.",
    )
    parser.add_argument(
        "--sample-rows",
        type=int,
        default=DEFAULT_SAMPLE_ROWS,
        help="Cantidad máxima de filas utilizadas como muestra.",
    )

    return parser.parse_args()


def main() -> int:
    """Punto de entrada del perfilador."""
    configure_logging()
    args = parse_arguments()

    try:
        if args.sample_rows <= 0:
            raise ValueError(
                "--sample-rows debe ser mayor que cero."
            )

        config = load_config(args.config)

        raw_data_dir = (
            PROJECT_ROOT
            / config["project"]["raw_data_dir"]
        )
        profiling_dir = (
            PROJECT_ROOT
            / "data"
            / "profiling"
        )

        dictionary_source = next(
            source
            for source in config["sources"]
            if source.get("resource_type") == "dictionary"
        )

        dictionary_path = (
            raw_data_dir
            / dictionary_source["resource_name"]
        )
        dictionary_variables = load_dictionary_variables(
            dictionary_path=dictionary_path,
            encoding=dictionary_source.get(
                "encoding",
                "utf-8-sig",
            ),
        )

        sources = select_sources(
            config=config,
            source_id=args.source_id,
            profile_all=args.all,
        )

        generated_reports = []
        for source in sources:
            report = profile_csv(
                source=source,
                raw_data_dir=raw_data_dir,
                dictionary_variables=dictionary_variables,
                sample_rows=args.sample_rows,
            )
            generated_reports.append(report)

            report_path = write_report(
                report=report,
                profiling_dir=profiling_dir,
            )

            logging.info(
                "%s | columnas=%s | muestra=%s | "
                "no documentadas=%s | devengado=%s",
                report["source_id"],
                report["column_count"],
                report["sample_rows_read"],
                report["undocumented_column_count"],
                report["devengado_column_count"],
            )
            logging.info(
                "Reporte generado: %s",
                report_path,
            )

        if len(generated_reports) > 1:
            comparison = compare_schemas(generated_reports)

            comparison_path = write_schema_comparison_report(
                comparison=comparison,
                profiling_dir=profiling_dir,
            )

            logging.info(
                "Comparación de esquemas | cantidad=%s | "
                "nombres=%s | orden=%s",
                comparison["all_same_column_count"],
                comparison["all_same_column_names"],
                comparison["all_same_column_order"],
            )
            logging.info(
                "Reporte consolidado: %s",
                comparison_path,
            )


        logging.info(
            "Perfilado ligero finalizado correctamente."
        )
        return 0

    except Exception as error:
        logging.exception(
            "El perfilado falló: %s",
            error,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())