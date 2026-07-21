"""Detección por bloques de filas completamente duplicadas."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import sqlite3
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from src.extract import (
    DEFAULT_CONFIG_PATH,
    PROJECT_ROOT,
    load_config,
)
from src.profile_sources import select_sources


DEFAULT_BATCH_ROWS = 50_000
DEFAULT_SAMPLE_LIMIT = 20

def configure_logging() -> None:
    """Configura los mensajes mostrados en consola."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def normalize_value(value: Any) -> str:
    """Convierte un valor en una representación estable para hashing."""
    if pd.isna(value):
        return "<NULL>"

    return str(value)


def calculate_values_hash(values: Iterable[Any]) -> str:
    """Calcula un SHA-256 estable para una secuencia de valores."""
    digest = hashlib.sha256()

    for value in values:
        encoded_value = normalize_value(value).encode("utf-8")

        digest.update(
            len(encoded_value).to_bytes(
                length=8,
                byteorder="big",
            )
        )
        digest.update(encoded_value)

    return digest.hexdigest()


def calculate_row_hash(row: pd.Series) -> str:
    """Calcula un hash SHA-256 estable a partir de una fila completa."""
    return calculate_values_hash(row.tolist())


def get_report_path(file_path: Path) -> str:
    """Obtiene una ruta portable para incluirla en el reporte."""
    try:
        return file_path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return file_path.as_posix()


def configure_database(
    connection: sqlite3.Connection,
) -> None:
    """Configura SQLite para una carga temporal eficiente."""
    connection.execute("PRAGMA journal_mode = OFF")
    connection.execute("PRAGMA synchronous = OFF")
    connection.execute("PRAGMA temp_store = MEMORY")
    connection.execute("PRAGMA locking_mode = EXCLUSIVE")

    connection.execute(
        """
        CREATE TABLE row_hashes (
            row_hash TEXT PRIMARY KEY,
            occurrence_count INTEGER NOT NULL
        )
        """
    )


def upsert_hash_batch(
    connection: sqlite3.Connection,
    hash_batch: list[tuple[str]],
) -> None:
    """Registra un lote de hashes e incrementa sus ocurrencias."""
    connection.executemany(
        """
        INSERT INTO row_hashes (
            row_hash,
            occurrence_count
        )
        VALUES (?, 1)
        ON CONFLICT(row_hash)
        DO UPDATE SET
            occurrence_count = occurrence_count + 1
        """,
        hash_batch,
    )
    connection.commit()

def write_duplicate_samples(
    source_file_path: Path,
    encoding: str,
    duplicate_hashes: set[str],
    output_path: Path,
) -> int:
    """Recupera las filas asociadas a los hashes duplicados seleccionados."""
    if not duplicate_hashes:
        return 0

    sampled_row_count = 0

    with source_file_path.open(
        "r",
        encoding=encoding,
        newline="",
    ) as source_file, output_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as output_file:
        reader = csv.reader(
            source_file,
            strict=True,
        )

        header = next(reader, None)

        if header is None:
            raise ValueError(
                "No se puede recuperar la muestra porque "
                "el archivo no contiene cabecera."
            )

        writer = csv.writer(output_file)
        writer.writerow(
            [
                "_ROW_NUMBER",
                "_ROW_HASH",
                *header,
            ]
        )

        for row_number, row in enumerate(
            reader,
            start=2,
        ):
            if not row:
                continue

            row_hash = calculate_values_hash(row)

            if row_hash not in duplicate_hashes:
                continue

            writer.writerow(
                [
                    row_number,
                    row_hash,
                    *row,
                ]
            )
            sampled_row_count += 1

    return sampled_row_count

def scan_duplicate_rows(
    source: dict[str, Any],
    raw_data_dir: Path,
    quality_dir: Path,
    batch_rows: int,
    keep_database: bool = False,
    sample_limit: int = DEFAULT_SAMPLE_LIMIT,
) -> dict[str, Any]:
    """Detecta filas duplicadas usando una base SQLite temporal."""
    if batch_rows <= 0:
        raise ValueError(
            "batch_rows debe ser mayor que cero."
        )
    if sample_limit < 0:
        raise ValueError(
            "sample_limit no puede ser negativo."
        )

    source_id = source["source_id"]
    resource_name = source["resource_name"]
    encoding = source.get("encoding", "utf-8-sig")
    file_path = raw_data_dir / resource_name

    if not file_path.exists():
        raise FileNotFoundError(
            f"No existe el archivo local para '{source_id}': "
            f"{file_path}"
        )

    quality_dir.mkdir(parents=True, exist_ok=True)

    database_descriptor, database_name = tempfile.mkstemp(
        prefix=f"{source_id}_duplicates_",
        suffix=".sqlite",
        dir=quality_dir,
    )
    os.close(database_descriptor)

    database_path = Path(database_name)
    connection: sqlite3.Connection | None = None

    row_count = 0
    batch_count = 0
    blank_row_count = 0
    malformed_row_count = 0

    try:
        connection = sqlite3.connect(database_path)
        configure_database(connection)

        logging.info(
            "Buscando duplicados en %s con lotes de %s filas.",
            resource_name,
            batch_rows,
        )

        with file_path.open(
            "r",
            encoding=encoding,
            newline="",
        ) as source_file:
            reader = csv.reader(
                source_file,
                strict=True,
            )

            header = next(reader, None)

            if header is None:
                raise ValueError(
                    f"La fuente '{source_id}' no contiene cabecera."
                )

            expected_column_count = len(header)
            hash_batch: list[tuple[str]] = []

            for row in reader:
                if not row:
                    blank_row_count += 1
                    continue

                row_count += 1

                if len(row) != expected_column_count:
                    malformed_row_count += 1

                row_hash = calculate_values_hash(row)
                hash_batch.append((row_hash,))

                if len(hash_batch) >= batch_rows:
                    upsert_hash_batch(
                        connection=connection,
                        hash_batch=hash_batch,
                    )

                    batch_count += 1
                    hash_batch.clear()

                    if batch_count % 10 == 0:
                        logging.info(
                            "%s | lotes=%s | filas procesadas=%s",
                            source_id,
                            batch_count,
                            f"{row_count:,}",
                        )

            if hash_batch:
                upsert_hash_batch(
                    connection=connection,
                    hash_batch=hash_batch,
                )
                batch_count += 1

        unique_row_count = int(
            connection.execute(
                """
                SELECT COUNT(*)
                FROM row_hashes
                """
            ).fetchone()[0]
        )

        duplicate_group_count = int(
            connection.execute(
                """
                SELECT COUNT(*)
                FROM row_hashes
                WHERE occurrence_count > 1
                """
            ).fetchone()[0]
        )

        duplicate_row_count = int(
            connection.execute(
                """
                SELECT COALESCE(
                    SUM(occurrence_count - 1),
                    0
                )
                FROM row_hashes
                WHERE occurrence_count > 1
                """
            ).fetchone()[0]
        )

        rows_in_duplicate_groups = int(
            connection.execute(
                """
                SELECT COALESCE(
                    SUM(occurrence_count),
                    0
                )
                FROM row_hashes
                WHERE occurrence_count > 1
                """
            ).fetchone()[0]
        )

        maximum_occurrence_count = int(
            connection.execute(
                """
                SELECT COALESCE(
                    MAX(occurrence_count),
                    1
                )
                FROM row_hashes
                """
            ).fetchone()[0]
        )

        duplicate_rate = (
            duplicate_row_count / row_count
            if row_count > 0
            else 0.0
        )

        duplicate_status = (
            "warning"
            if duplicate_row_count > 0
            else "passed"
        )
        sampled_duplicate_group_count = 0
        sampled_row_count = 0
        duplicate_sample_path: str | None = None

        if duplicate_group_count > 0 and sample_limit > 0:
            duplicate_hash_rows = connection.execute(
                """
                SELECT row_hash
                FROM row_hashes
                WHERE occurrence_count > 1
                ORDER BY occurrence_count DESC, row_hash
                LIMIT ?
                """,
                (sample_limit,),
            ).fetchall()

            duplicate_hashes = {
                str(row[0])
                for row in duplicate_hash_rows
            }

            sampled_duplicate_group_count = len(
                duplicate_hashes
            )

            sample_timestamp = datetime.now(UTC).strftime(
                "%Y%m%dT%H%M%S%fZ"
            )
            sample_path = (
                quality_dir
                / (
                    f"{sample_timestamp}_{source_id}"
                    "_duplicate_samples.csv"
                )
            )

            sampled_row_count = write_duplicate_samples(
                source_file_path=file_path,
                encoding=encoding,
                duplicate_hashes=duplicate_hashes,
                output_path=sample_path,
            )

            duplicate_sample_path = get_report_path(
                sample_path
            )
        return {
            "source_id": source_id,
            "resource_name": resource_name,
            "reference_year": source.get("reference_year"),
            "local_path": get_report_path(file_path),
            "file_size_bytes": file_path.stat().st_size,
            "configured_encoding": encoding,
            "header_column_count": expected_column_count,
            "batch_rows": batch_rows,
            "batch_count": batch_count,
            "row_count": row_count,
            "unique_row_count": unique_row_count,
            "duplicate_group_count": duplicate_group_count,
            "duplicate_row_count": duplicate_row_count,
            "rows_in_duplicate_groups": (
                rows_in_duplicate_groups
            ),
            "duplicate_rate": round(
                duplicate_rate,
                10,
            ),
            "maximum_occurrence_count": (
                maximum_occurrence_count
            ),
            "sample_limit": sample_limit,
            "sampled_duplicate_group_count": (
                sampled_duplicate_group_count
            ),
            "sampled_row_count": sampled_row_count,
            "duplicate_sample_path": duplicate_sample_path,
            "blank_row_count": blank_row_count,
            "malformed_row_count": malformed_row_count,
            "duplicate_control": {
                "severity": "warning",
                "status": duplicate_status,
                "rule": (
                    "Una fila se considera duplicada cuando todos "
                    "sus campos coinciden con otra fila."
                ),
                "hash_algorithm": "SHA-256",
            },
            "temporary_database_kept": keep_database,
            "temporary_database_path": (
                get_report_path(database_path)
                if keep_database
                else None
            ),
            "checked_at_utc": datetime.now(UTC).isoformat(),
            "quality_version": "0.1.0",
        }

    finally:
        if connection is not None:
            connection.close()

        if not keep_database:
            database_path.unlink(missing_ok=True)


def write_duplicate_report(
    report: dict[str, Any],
    quality_dir: Path,
) -> Path:
    """Guarda el reporte de duplicados en formato JSON."""
    quality_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    source_id = report["source_id"]

    report_path = (
        quality_dir
        / f"{timestamp}_{source_id}_duplicates.json"
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
            "Detecta filas completamente duplicadas mediante "
            "hashes y una base SQLite temporal."
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
        help="Evalúa los recursos 2024, 2025 y 2026.",
    )
    parser.add_argument(
        "--batch-rows",
        type=int,
        default=DEFAULT_BATCH_ROWS,
        help="Cantidad de hashes registrados en cada lote.",
    )
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=DEFAULT_SAMPLE_LIMIT,
        help=(
            "Máximo de grupos duplicados cuyas filas "
            "se incluirán en el CSV de muestra."
        ),
    )
    parser.add_argument(
        "--keep-database",
        action="store_true",
        help="Conserva la base SQLite temporal después del análisis.",
    )

    return parser.parse_args()


def main() -> int:
    """Punto de entrada de la detección de duplicados."""
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
            report = scan_duplicate_rows(
                source=source,
                raw_data_dir=raw_data_dir,
                quality_dir=quality_dir,
                batch_rows=args.batch_rows,
                keep_database=args.keep_database,
                sample_limit=args.sample_limit,
            )

            report_path = write_duplicate_report(
                report=report,
                quality_dir=quality_dir,
            )

            logging.info(
                "%s | filas=%s | únicas=%s | "
                "duplicadas=%s | grupos=%s",
                report["source_id"],
                f"{report['row_count']:,}",
                f"{report['unique_row_count']:,}",
                f"{report['duplicate_row_count']:,}",
                f"{report['duplicate_group_count']:,}",
            )
            logging.info(
                "Reporte generado: %s",
                report_path,
            )
            if report["duplicate_sample_path"]:
                logging.info(
                    "Muestra de duplicados: %s",
                    report["duplicate_sample_path"],
                )

        logging.info(
            "Detección de duplicados finalizada correctamente."
        )
        return 0

    except Exception as error:
        logging.exception(
            "La detección de duplicados falló: %s",
            error,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())