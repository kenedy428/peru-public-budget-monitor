"""Verifica la integridad de los archivos fuente descargados."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

from src.extract import (
    DEFAULT_CONFIG_PATH,
    PROJECT_ROOT,
    calculate_sha256,
    load_config,
)


VALID_MANIFEST_STATUSES = {
    "success",
    "updated",
    "refreshed",
    "unchanged",
    "skipped_existing",
}


def configure_logging() -> None:
    """Configura los mensajes mostrados en consola."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def find_latest_manifest(
    manifest_dir: Path,
    source_id: str,
) -> Path:
    """Localiza el manifiesto más reciente de una fuente."""
    candidates = list(manifest_dir.glob(f"*_{source_id}.json"))

    if not candidates:
        raise FileNotFoundError(
            f"No existe un manifiesto para la fuente '{source_id}'."
        )

    return max(candidates, key=lambda path: path.stat().st_mtime)


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    """Carga un manifiesto JSON."""
    with manifest_path.open("r", encoding="utf-8") as file:
        manifest = json.load(file)

    if not isinstance(manifest, dict):
        raise ValueError(
            f"El manifiesto no contiene un objeto válido: {manifest_path}"
        )

    return manifest


def verify_source(
    source: dict[str, Any],
    raw_data_dir: Path,
    manifest_dir: Path,
    check_hash: bool = True,
) -> dict[str, Any]:
    """Compara un archivo local contra su manifiesto más reciente."""
    source_id = source["source_id"]
    target_path = raw_data_dir / source["resource_name"]

    manifest_path = find_latest_manifest(
        manifest_dir=manifest_dir,
        source_id=source_id,
    )
    manifest = load_manifest(manifest_path)

    manifest_status = manifest.get("status")

    if manifest_status not in VALID_MANIFEST_STATUSES:
        return {
            "source_id": source_id,
            "verified": False,
            "reason": f"Estado de manifiesto no válido: {manifest_status}",
            "manifest_path": manifest_path,
        }

    if not target_path.exists():
        return {
            "source_id": source_id,
            "verified": False,
            "reason": "El archivo local no existe.",
            "manifest_path": manifest_path,
        }

    expected_size = manifest.get("file_size_bytes")
    expected_hash = manifest.get("sha256_hash")

    actual_size = target_path.stat().st_size
    size_matches = expected_size == actual_size

    actual_hash: str | None = None
    hash_matches: bool | None = None

    if check_hash:
        actual_hash = calculate_sha256(target_path)
        hash_matches = expected_hash == actual_hash

    verified = size_matches and (
        hash_matches is True if check_hash else True
    )

    return {
        "source_id": source_id,
        "resource_name": source["resource_name"],
        "verified": verified,
        "manifest_status": manifest_status,
        "expected_size_bytes": expected_size,
        "actual_size_bytes": actual_size,
        "size_matches": size_matches,
        "expected_sha256_hash": expected_hash,
        "actual_sha256_hash": actual_hash,
        "hash_matches": hash_matches,
        "manifest_path": manifest_path,
        "local_path": target_path,
    }


def parse_arguments() -> argparse.Namespace:
    """Define los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Verifica archivos locales contra sus manifiestos."
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Ruta del archivo YAML de configuración.",
    )
    parser.add_argument(
        "--source-id",
        help="Verifica únicamente una fuente determinada.",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Verifica solamente existencia y tamaño, sin calcular hash.",
    )

    return parser.parse_args()


def main() -> int:
    """Punto de entrada del verificador."""
    configure_logging()
    args = parse_arguments()

    try:
        config = load_config(args.config)

        raw_data_dir = (
            PROJECT_ROOT / config["project"]["raw_data_dir"]
        )
        manifest_dir = (
            PROJECT_ROOT / config["project"]["manifest_dir"]
        )

        sources = config["sources"]

        if args.source_id:
            sources = [
                source
                for source in sources
                if source["source_id"] == args.source_id
            ]

            if not sources:
                raise ValueError(
                    f"No existe la fuente '{args.source_id}'."
                )

        results = [
            verify_source(
                source=source,
                raw_data_dir=raw_data_dir,
                manifest_dir=manifest_dir,
                check_hash=not args.quick,
            )
            for source in sources
        ]

        for result in results:
            state = "OK" if result["verified"] else "FAILED"
            hash_state = (
                "omitido"
                if result.get("hash_matches") is None
                else str(result["hash_matches"])
            )

            logging.info(
                "%s | %s | tamaño=%s | hash=%s",
                result["source_id"],
                state,
                result.get("size_matches"),
                hash_state,
            )

            if not result["verified"]:
                logging.error(
                    "Motivo: %s",
                    result.get("reason", "No coincide con el manifiesto."),
                )

        if all(result["verified"] for result in results):
            logging.info(
                "Todos los archivos seleccionados fueron verificados."
            )
            return 0

        logging.error("Una o más fuentes no superaron la verificación.")
        return 1

    except Exception as error:
        logging.exception("La verificación falló: %s", error)
        return 1


if __name__ == "__main__":
    sys.exit(main())