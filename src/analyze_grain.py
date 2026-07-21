"""Análisis exacto del grano y de claves candidatas."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sqlite3
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.check_duplicates import calculate_values_hash
from src.extract import (
    DEFAULT_CONFIG_PATH,
    PROJECT_ROOT,
    load_config,
)
from src.profile_sources import select_sources


DEFAULT_BATCH_ROWS = 50_000

MAXIMAL_TECHNICAL_KEY = (
    "ANO_EJE",
    "NIVEL_GOBIERNO",
    "SECTOR",
    "PLIEGO",
    "SEC_EJEC",
    "EJECUTORA",
    "DEPARTAMENTO_EJECUTORA",
    "PROVINCIA_EJECUTORA",
    "DISTRITO_EJECUTORA",
    "PROGRAMA_PPTO",
    "TIPO_ACT_PROY",
    "PRODUCTO_PROYECTO",
    "ACTIVIDAD_ACCION_OBRA",
    "FUNCION",
    "DIVISION_FUNCIONAL",
    "GRUPO_FUNCIONAL",
    "SEC_FUNC",
    "META",
    "FINALIDAD",
    "DEPARTAMENTO_META",
    "FUENTE_FINANCIAMIENTO",
    "RUBRO",
    "TIPO_RECURSO",
    "CATEGORIA_GASTO",
    "TIPO_TRANSACCION",
    "GENERICA",
    "SUBGENERICA",
    "SUBGENERICA_DET",
    "ESPECIFICA",
    "ESPECIFICA_DET",
)

BUSINESS_KEY_V1 = (
    "ANO_EJE",
    "SEC_EJEC",
    "EJECUTORA",
    "PROGRAMA_PPTO",
    "TIPO_ACT_PROY",
    "PRODUCTO_PROYECTO",
    "ACTIVIDAD_ACCION_OBRA",
    "FUNCION",
    "DIVISION_FUNCIONAL",
    "GRUPO_FUNCIONAL",
    "SEC_FUNC",
    "META",
    "FINALIDAD",
    "DEPARTAMENTO_META",
    "FUENTE_FINANCIAMIENTO",
    "RUBRO",
    "TIPO_RECURSO",
    "CATEGORIA_GASTO",
    "TIPO_TRANSACCION",
    "GENERICA",
    "SUBGENERICA",
    "SUBGENERICA_DET",
    "ESPECIFICA",
    "ESPECIFICA_DET",
)

DEFAULT_CANDIDATE_KEYS = {
    "maximal_technical_key": MAXIMAL_TECHNICAL_KEY,
    "business_key_v1": BUSINESS_KEY_V1,
}


def configure_logging() -> None:
    """Configura los mensajes mostrados en consola."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def configure_database(
    connection: sqlite3.Connection,
) -> None:
    """Configura la base temporal para registrar claves."""
    connection.execute("PRAGMA journal_mode = OFF")
    connection.execute("PRAGMA synchronous = OFF")
    connection.execute("PRAGMA temp_store = MEMORY")
    connection.execute("PRAGMA locking_mode = EXCLUSIVE")

    connection.execute(
        """
        CREATE TABLE candidate_key_hashes (
            key_name TEXT NOT NULL,
            key_hash TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            PRIMARY KEY (key_name, key_hash)
        ) WITHOUT ROWID
        """
    )


def validate_candidate_columns(
    header: list[str],
    candidate_keys: dict[str, tuple[str, ...]],
) -> None:
    """Comprueba que todas las columnas candidatas existan."""
    header_set = set(header)

    for key_name, columns in candidate_keys.items():
        missing_columns = [
            column
            for column in columns
            if column not in header_set
        ]

        if missing_columns:
            raise ValueError(
                f"La clave '{key_name}' usa columnas inexistentes: "
                f"{missing_columns}"
            )


def upsert_hash_batch(
    connection: sqlite3.Connection,
    hash_batch: list[tuple[str, str]],
) -> None:
    """Registra un lote de hashes de claves candidatas."""
    connection.executemany(
        """
        INSERT INTO candidate_key_hashes (
            key_name,
            key_hash,
            occurrence_count
        )
        VALUES (?, ?, 1)
        ON CONFLICT(key_name, key_hash)
        DO UPDATE SET
            occurrence_count = occurrence_count + 1
        """,
        hash_batch,
    )
    connection.commit()


def summarize_candidate_key(
    connection: sqlite3.Connection,
    key_name: str,
    analyzed_row_count: int,
) -> dict[str, Any]:
    """Obtiene las métricas de unicidad de una clave candidata."""
    unique_key_count = int(
        connection.execute(
            """
            SELECT COUNT(*)
            FROM candidate_key_hashes
            WHERE key_name = ?
            """,
            (key_name,),
        ).fetchone()[0]
    )

    duplicate_group_count = int(
        connection.execute(
            """
            SELECT COUNT(*)
            FROM candidate_key_hashes
            WHERE key_name = ?
              AND occurrence_count > 1
            """,
            (key_name,),
        ).fetchone()[0]
    )

    duplicate_key_row_count = int(
        connection.execute(
            """
            SELECT COALESCE(
                SUM(occurrence_count - 1),
                0
            )
            FROM candidate_key_hashes
            WHERE key_name = ?
              AND occurrence_count > 1
            """,
            (key_name,),
        ).fetchone()[0]
    )

    rows_in_duplicate_groups = int(
        connection.execute(
            """
            SELECT COALESCE(
                SUM(occurrence_count),
                0
            )
            FROM candidate_key_hashes
            WHERE key_name = ?
              AND occurrence_count > 1
            """,
            (key_name,),
        ).fetchone()[0]
    )

    maximum_occurrence_count = int(
        connection.execute(
            """
            SELECT COALESCE(
                MAX(occurrence_count),
                0
            )
            FROM candidate_key_hashes
            WHERE key_name = ?
            """,
            (key_name,),
        ).fetchone()[0]
    )

    duplicate_rate = (
        duplicate_key_row_count / analyzed_row_count
        if analyzed_row_count > 0
        else 0.0
    )

    return {
        "unique_key_count": unique_key_count,
        "duplicate_group_count": duplicate_group_count,
        "duplicate_key_row_count": duplicate_key_row_count,
        "rows_in_duplicate_groups": rows_in_duplicate_groups,
        "maximum_occurrence_count": maximum_occurrence_count,
        "duplicate_rate": round(duplicate_rate, 10),
    }


def analyze_candidate_keys(
    source: dict[str, Any],
    raw_data_dir: Path,
    profiling_dir: Path,
    batch_rows: int,
    candidate_keys: dict[str, tuple[str, ...]] | None = None,
) -> dict[str, Any]:
    """Evalúa la unicidad de varias claves en un único recorrido."""
    if batch_rows <= 0:
        raise ValueError(
            "batch_rows debe ser mayor que cero."
        )

    if candidate_keys is None:
        candidate_keys = DEFAULT_CANDIDATE_KEYS

    source_id = source["source_id"]
    resource_name = source["resource_name"]
    encoding = source.get("encoding", "utf-8-sig")
    file_path = raw_data_dir / resource_name

    if not file_path.exists():
        raise FileNotFoundError(
            f"No existe el archivo de '{source_id}': {file_path}"
        )

    profiling_dir.mkdir(parents=True, exist_ok=True)

    descriptor, database_name = tempfile.mkstemp(
        prefix=f"{source_id}_grain_",
        suffix=".sqlite",
        dir=profiling_dir,
    )
    os.close(descriptor)

    database_path = Path(database_name)
    connection: sqlite3.Connection | None = None

    row_count = 0
    analyzed_row_count = 0
    blank_row_count = 0
    malformed_row_count = 0
    batch_count = 0

    try:
        connection = sqlite3.connect(database_path)
        configure_database(connection)

        logging.info(
            "Analizando grano de %s con lotes de %s filas.",
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

            validate_candidate_columns(
                header=header,
                candidate_keys=candidate_keys,
            )

            column_indexes = {
                column: index
                for index, column in enumerate(header)
            }

            expected_column_count = len(header)
            hash_batch: list[tuple[str, str]] = []
            rows_in_current_batch = 0

            for row in reader:
                if not row:
                    blank_row_count += 1
                    continue

                row_count += 1

                if len(row) != expected_column_count:
                    malformed_row_count += 1
                    continue

                analyzed_row_count += 1

                for key_name, key_columns in candidate_keys.items():
                    key_values = (
                        row[column_indexes[column]]
                        for column in key_columns
                    )

                    key_hash = calculate_values_hash(
                        key_values
                    )

                    hash_batch.append(
                        (
                            key_name,
                            key_hash,
                        )
                    )

                rows_in_current_batch += 1

                if rows_in_current_batch >= batch_rows:
                    upsert_hash_batch(
                        connection=connection,
                        hash_batch=hash_batch,
                    )

                    batch_count += 1
                    hash_batch.clear()
                    rows_in_current_batch = 0

                    if batch_count % 10 == 0:
                        logging.info(
                            "%s | lotes=%s | filas=%s",
                            source_id,
                            batch_count,
                            f"{analyzed_row_count:,}",
                        )

            if hash_batch:
                upsert_hash_batch(
                    connection=connection,
                    hash_batch=hash_batch,
                )
                batch_count += 1

        key_results = {
            key_name: {
                "columns": list(key_columns),
                "column_count": len(key_columns),
                **summarize_candidate_key(
                    connection=connection,
                    key_name=key_name,
                    analyzed_row_count=analyzed_row_count,
                ),
            }
            for key_name, key_columns in candidate_keys.items()
        }

        return {
            "source_id": source_id,
            "resource_name": resource_name,
            "reference_year": source.get("reference_year"),
            "row_count": row_count,
            "analyzed_row_count": analyzed_row_count,
            "blank_row_count": blank_row_count,
            "malformed_row_count": malformed_row_count,
            "batch_rows": batch_rows,
            "batch_count": batch_count,
            "candidate_keys": key_results,
            "analyzed_at_utc": datetime.now(UTC).isoformat(),
            "analysis_version": "0.1.0",
        }

    finally:
        if connection is not None:
            connection.close()

        database_path.unlink(missing_ok=True)


def write_report(
    report: dict[str, Any],
    profiling_dir: Path,
) -> Path:
    """Guarda el análisis del grano en formato JSON."""
    timestamp = datetime.now(UTC).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )

    report_path = (
        profiling_dir
        / (
            f"{timestamp}_{report['source_id']}"
            "_grain_analysis.json"
        )
    )

    report_path.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return report_path


def parse_arguments() -> argparse.Namespace:
    """Define los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description=(
            "Analiza la unicidad de claves candidatas para "
            "determinar el grano de las fuentes."
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
        help="Identificador de una fuente.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Analiza 2024, 2025 y 2026.",
    )
    parser.add_argument(
        "--batch-rows",
        type=int,
        default=DEFAULT_BATCH_ROWS,
        help="Cantidad de filas procesadas por lote.",
    )

    return parser.parse_args()


def main() -> int:
    """Punto de entrada del análisis de grano."""
    configure_logging()
    args = parse_arguments()

    try:
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
            report = analyze_candidate_keys(
                source=source,
                raw_data_dir=raw_data_dir,
                profiling_dir=profiling_dir,
                batch_rows=args.batch_rows,
            )

            report_path = write_report(
                report=report,
                profiling_dir=profiling_dir,
            )

            logging.info(
                "%s | filas analizadas=%s",
                report["source_id"],
                f"{report['analyzed_row_count']:,}",
            )

            for key_name, result in report[
                "candidate_keys"
            ].items():
                logging.info(
                    "%s | columnas=%s | únicas=%s | "
                    "duplicadas=%s | grupos=%s",
                    key_name,
                    result["column_count"],
                    f"{result['unique_key_count']:,}",
                    f"{result['duplicate_key_row_count']:,}",
                    f"{result['duplicate_group_count']:,}",
                )

            logging.info(
                "Reporte generado: %s",
                report_path,
            )

        logging.info(
            "Análisis de grano finalizado correctamente."
        )
        return 0

    except Exception as error:
        logging.exception(
            "El análisis de grano falló: %s",
            error,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())