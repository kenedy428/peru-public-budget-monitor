"""Escaneo por bloques del contenido de las fuentes oficiales del MEF."""

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


def scan_csv_content(
    source: dict[str, Any],
    raw_data_dir: Path,
    chunk_rows: int,
) -> dict[str, Any]:
    """Cuenta filas y revisa cobertura mensual mediante bloques."""
    if chunk_rows <= 0:
        raise ValueError("chunk_rows debe ser mayor que cero.")

    source_id = source["source_id"]
    resource_name = source["resource_name"]
    encoding = source.get("encoding", "utf-8-sig")
    file_path = raw_data_dir / resource_name

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

    (
        monthly_columns,
        _annual_columns,
        _other_devengado_columns,
    ) = classify_devengado_columns(columns)

    if not monthly_columns:
        raise ValueError(
            f"La fuente '{source_id}' no contiene columnas mensuales "
            "de Devengado."
        )

    monthly_stats = {
        column: {
            "non_null_count": 0,
            "null_count": 0,
            "zero_count": 0,
            "non_zero_count": 0,
        }
        for column in monthly_columns
    }

    row_count = 0
    chunk_count = 0

    logging.info(
        "Escaneando %s en bloques de %s filas.",
        resource_name,
        chunk_rows,
    )

    chunks = pd.read_csv(
        file_path,
        encoding=encoding,
        usecols=monthly_columns,
        chunksize=chunk_rows,
        low_memory=False,
    )

    for chunk in chunks:
        chunk_count += 1
        row_count += len(chunk)

        for column in monthly_columns:
            values = pd.to_numeric(
                chunk[column],
                errors="coerce",
            )

            non_null_mask = values.notna()
            zero_mask = non_null_mask & values.eq(0)
            non_zero_mask = non_null_mask & values.ne(0)

            monthly_stats[column]["non_null_count"] += int(
                non_null_mask.sum()
            )
            monthly_stats[column]["null_count"] += int(
                values.isna().sum()
            )
            monthly_stats[column]["zero_count"] += int(
                zero_mask.sum()
            )
            monthly_stats[column]["non_zero_count"] += int(
                non_zero_mask.sum()
            )

        if chunk_count % 10 == 0:
            logging.info(
                "%s | bloques=%s | filas procesadas=%s",
                source_id,
                chunk_count,
                f"{row_count:,}",
            )

    populated_month_columns = [
        column
        for column in monthly_columns
        if monthly_stats[column]["non_zero_count"] > 0
    ]

    last_populated_month_column = (
        populated_month_columns[-1]
        if populated_month_columns
        else None
    )

    last_populated_month = (
        last_populated_month_column.removeprefix(
            "MONTO_DEVENGADO_"
        )
        if last_populated_month_column
        else None
    )

    return {
        "source_id": source_id,
        "resource_name": resource_name,
        "reference_year": source.get("reference_year"),
        "local_path": get_report_path(file_path),
        "file_size_bytes": file_path.stat().st_size,
        "configured_encoding": encoding,
        "chunk_rows": chunk_rows,
        "chunk_count": chunk_count,
        "row_count": row_count,
        "monthly_column_count": len(monthly_columns),
        "monthly_columns": monthly_columns,
        "monthly_stats": monthly_stats,
        "populated_month_columns": populated_month_columns,
        "last_populated_month_column": last_populated_month_column,
        "last_populated_month": last_populated_month,
        "last_month_rule": (
            "Último mes cuya columna contiene al menos un monto "
            "distinto de cero."
        ),
        "scanned_at_utc": datetime.now(UTC).isoformat(),
        "profiling_version": "0.1.0",
    }


def write_scan_report(
    report: dict[str, Any],
    profiling_dir: Path,
) -> Path:
    """Guarda el reporte del escaneo en formato JSON."""
    profiling_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    source_id = report["source_id"]

    report_path = (
        profiling_dir
        / f"{timestamp}_{source_id}_content_scan.json"
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
            "Cuenta filas y revisa la cobertura mensual "
            "de las fuentes del MEF mediante bloques."
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
        help="Escanea los recursos 2024, 2025 y 2026.",
    )
    parser.add_argument(
        "--chunk-rows",
        type=int,
        default=DEFAULT_CHUNK_ROWS,
        help="Cantidad de filas procesadas en cada bloque.",
    )

    return parser.parse_args()


def main() -> int:
    """Punto de entrada del escaneo de contenido."""
    configure_logging()
    args = parse_arguments()

    try:
        if args.chunk_rows <= 0:
            raise ValueError(
                "--chunk-rows debe ser mayor que cero."
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

        sources = select_sources(
            config=config,
            source_id=args.source_id,
            profile_all=args.all,
        )

        for source in sources:
            report = scan_csv_content(
                source=source,
                raw_data_dir=raw_data_dir,
                chunk_rows=args.chunk_rows,
            )

            report_path = write_scan_report(
                report=report,
                profiling_dir=profiling_dir,
            )

            logging.info(
                "%s | filas=%s | bloques=%s | último mes=%s",
                report["source_id"],
                f"{report['row_count']:,}",
                report["chunk_count"],
                report["last_populated_month"],
            )
            logging.info(
                "Reporte generado: %s",
                report_path,
            )

        logging.info(
            "Escaneo de contenido finalizado correctamente."
        )
        return 0

    except Exception as error:
        logging.exception(
            "El escaneo de contenido falló: %s",
            error,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())