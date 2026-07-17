"""Descarga reproducible de los archivos fuente oficiales del MEF."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "sources.yaml"
CHUNK_SIZE_BYTES = 1024 * 1024  # 1 MB


def configure_logging() -> None:
    """Configura mensajes básicos del proceso en consola."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def load_config(config_path: Path) -> dict[str, Any]:
    """Carga y valida la estructura principal del archivo YAML."""
    if not config_path.exists():
        raise FileNotFoundError(f"No existe el archivo de configuración: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError("La configuración YAML no contiene un objeto válido.")

    if "project" not in config or "sources" not in config:
        raise ValueError("La configuración debe contener 'project' y 'sources'.")

    if not isinstance(config["sources"], list) or not config["sources"]:
        raise ValueError("La configuración no contiene fuentes válidas.")

    return config


def calculate_sha256(file_path: Path) -> str:
    """Calcula el hash SHA-256 de un archivo existente."""
    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(CHUNK_SIZE_BYTES), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def validate_download(
    file_path: Path,
    expected_size: int | None,
    actual_size: int,
    file_format: str,
) -> None:
    """Comprueba tamaño y contenido básico de la descarga."""
    if actual_size == 0:
        raise ValueError("El archivo descargado está vacío.")

    if expected_size is not None and expected_size != actual_size:
        raise ValueError(
            "La descarga está incompleta: "
            f"se esperaban {expected_size} bytes y se recibieron {actual_size}."
        )

    with file_path.open("rb") as file:
        first_bytes = file.read(512).lstrip().lower()

    if first_bytes.startswith(b"<!doctype html") or first_bytes.startswith(b"<html"):
        raise ValueError(
            "La URL devolvió contenido HTML en lugar del archivo esperado."
        )

    if file_format.lower() == "csv" and b"," not in first_bytes:
        raise ValueError(
            "El archivo no presenta una estructura CSV reconocible en su cabecera."
        )


def write_manifest(manifest: dict[str, Any], manifest_dir: Path) -> Path:
    """Guarda el manifiesto JSON de una ejecución."""
    manifest_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    source_id = manifest["source_id"]
    manifest_path = manifest_dir / f"{timestamp}_{source_id}.json"

    with manifest_path.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, ensure_ascii=False, indent=2)

    return manifest_path


def download_source(
    source: dict[str, Any],
    raw_data_dir: Path,
    manifest_dir: Path,
    force: bool = False,
) -> dict[str, Any]:
    """Descarga una fuente, calcula su hash y genera un manifiesto."""
    source_id = source["source_id"]
    resource_name = source["resource_name"]
    download_url = source["download_url"]
    file_format = source.get("file_format", "")

    raw_data_dir.mkdir(parents=True, exist_ok=True)

    target_path = raw_data_dir / resource_name
    temporary_path = target_path.with_suffix(f"{target_path.suffix}.part")

    started_at = datetime.now(UTC)
    start_time = time.perf_counter()

    if target_path.exists() and not force:
        logging.info(
            "El archivo %s ya existe. Se conservará la copia local.",
            resource_name,
        )

        manifest = {
            "source_id": source_id,
            "resource_name": resource_name,
            "reference_year": source.get("reference_year"),
            "source_url": source.get("page_url"),
            "download_url": download_url,
            "resource_id": source.get("resource_id"),
            "download_timestamp_utc": started_at.isoformat(),
            "local_path": target_path.relative_to(PROJECT_ROOT).as_posix(),
            "file_size_bytes": target_path.stat().st_size,
            "sha256_hash": calculate_sha256(target_path),
            "status": "skipped_existing",
            "pipeline_version": "0.1.0",
        }

        manifest_path = write_manifest(manifest, manifest_dir)
        logging.info("Manifiesto generado: %s", manifest_path)
        return manifest

    logging.info("Descargando %s", resource_name)
    logging.info("URL: %s", download_url)

    sha256 = hashlib.sha256()
    bytes_written = 0

    headers = {
        "User-Agent": "peru-public-budget-monitor/0.1.0",
    }

    try:
        with requests.get(
            download_url,
            stream=True,
            timeout=(15, 300),
            headers=headers,
        ) as response:
            response.raise_for_status()

            content_length = response.headers.get("Content-Length")
            expected_size = int(content_length) if content_length else None
            content_type = response.headers.get("Content-Type")

            with temporary_path.open("wb") as file:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE_BYTES):
                    if not chunk:
                        continue

                    file.write(chunk)
                    sha256.update(chunk)
                    bytes_written += len(chunk)

        validate_download(
            file_path=temporary_path,
            expected_size=expected_size,
            actual_size=bytes_written,
            file_format=file_format,
        )

        # Reemplaza el destino únicamente después de validar la descarga.
        temporary_path.replace(target_path)

        finished_at = datetime.now(UTC)
        runtime_seconds = round(time.perf_counter() - start_time, 3)

        manifest = {
            "source_id": source_id,
            "resource_name": resource_name,
            "resource_type": source.get("resource_type"),
            "reference_year": source.get("reference_year"),
            "source_url": source.get("page_url"),
            "download_url": download_url,
            "resource_id": source.get("resource_id"),
            "download_timestamp_utc": finished_at.isoformat(),
            "local_path": target_path.relative_to(PROJECT_ROOT).as_posix(),
            "file_format": file_format,
            "configured_encoding": source.get("encoding"),
            "content_type": content_type,
            "expected_size_bytes": expected_size,
            "file_size_bytes": bytes_written,
            "sha256_hash": sha256.hexdigest(),
            "runtime_seconds": runtime_seconds,
            "mutable_source": source.get("mutable"),
            "status": "success",
            "pipeline_version": "0.1.0",
        }

        manifest_path = write_manifest(manifest, manifest_dir)

        logging.info("Descarga completada: %s", target_path)
        logging.info("Tamaño: %s bytes", bytes_written)
        logging.info("SHA-256: %s", sha256.hexdigest())
        logging.info("Manifiesto: %s", manifest_path)

        return manifest

    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def select_sources(
    config: dict[str, Any],
    source_id: str | None,
    download_all: bool,
) -> list[dict[str, Any]]:
    """Selecciona una fuente concreta o todas las configuradas."""
    sources = config["sources"]

    if download_all:
        return sources

    selected_id = source_id or "mef_devengado_dictionary"

    selected = [
        source for source in sources if source["source_id"] == selected_id
    ]

    if not selected:
        available = ", ".join(source["source_id"] for source in sources)
        raise ValueError(
            f"No existe la fuente '{selected_id}'. "
            f"Fuentes disponibles: {available}"
        )

    return selected


def parse_arguments() -> argparse.Namespace:
    """Define los argumentos disponibles en la línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Descarga reproducible de fuentes oficiales del MEF."
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Ruta del archivo YAML de configuración.",
    )
    parser.add_argument(
        "--source-id",
        help="Identificador de una fuente configurada.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Descarga todas las fuentes configuradas.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reemplaza el archivo local si ya existe.",
    )

    return parser.parse_args()


def main() -> int:
    """Punto de entrada del proceso de ingesta."""
    configure_logging()
    args = parse_arguments()

    try:
        config = load_config(args.config)

        raw_data_dir = PROJECT_ROOT / config["project"]["raw_data_dir"]
        manifest_dir = PROJECT_ROOT / config["project"]["manifest_dir"]

        selected_sources = select_sources(
            config=config,
            source_id=args.source_id,
            download_all=args.all,
        )

        for source in selected_sources:
            download_source(
                source=source,
                raw_data_dir=raw_data_dir,
                manifest_dir=manifest_dir,
                force=args.force,
            )

        logging.info("Proceso finalizado correctamente.")
        return 0

    except Exception as error:
        logging.exception("El proceso de ingesta falló: %s", error)
        return 1


if __name__ == "__main__":
    sys.exit(main())