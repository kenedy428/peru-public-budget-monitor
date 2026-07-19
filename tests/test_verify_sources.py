"""Pruebas unitarias para la verificación de archivos fuente."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from src.verify_sources import (
    find_latest_manifest,
    verify_source,
)


def write_test_manifest(
    manifest_path: Path,
    *,
    source_id: str,
    status: str,
    file_size_bytes: int,
    sha256_hash: str,
) -> None:
    """Crea un manifiesto mínimo para las pruebas."""
    manifest = {
        "source_id": source_id,
        "status": status,
        "file_size_bytes": file_size_bytes,
        "sha256_hash": sha256_hash,
    }

    manifest_path.write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )


def test_find_latest_manifest_returns_newest_file(
    tmp_path: Path,
) -> None:
    """Debe seleccionarse el manifiesto más reciente."""
    manifest_dir = tmp_path / "manifests"
    manifest_dir.mkdir()

    old_manifest = (
        manifest_dir / "20260101T000000000000Z_test_source.json"
    )
    new_manifest = (
        manifest_dir / "20260102T000000000000Z_test_source.json"
    )

    old_manifest.write_text("{}", encoding="utf-8")
    new_manifest.write_text("{}", encoding="utf-8")

    os.utime(old_manifest, (1_000, 1_000))
    os.utime(new_manifest, (2_000, 2_000))

    result = find_latest_manifest(
        manifest_dir=manifest_dir,
        source_id="test_source",
    )

    assert result == new_manifest


def test_verify_source_quick_accepts_matching_size(
    tmp_path: Path,
) -> None:
    """La verificación rápida debe comprobar existencia y tamaño."""
    raw_dir = tmp_path / "raw"
    manifest_dir = tmp_path / "manifests"
    raw_dir.mkdir()
    manifest_dir.mkdir()

    content = b"column_a,column_b\n1,2\n"
    source_file = raw_dir / "sample.csv"
    source_file.write_bytes(content)

    expected_hash = hashlib.sha256(content).hexdigest()

    manifest_path = (
        manifest_dir
        / "20260101T000000000000Z_test_source.json"
    )
    write_test_manifest(
        manifest_path,
        source_id="test_source",
        status="success",
        file_size_bytes=len(content),
        sha256_hash=expected_hash,
    )

    source = {
        "source_id": "test_source",
        "resource_name": "sample.csv",
    }

    result = verify_source(
        source=source,
        raw_data_dir=raw_dir,
        manifest_dir=manifest_dir,
        check_hash=False,
    )

    assert result["verified"] is True
    assert result["size_matches"] is True
    assert result["hash_matches"] is None


def test_verify_source_rejects_missing_file(
    tmp_path: Path,
) -> None:
    """Debe fallar cuando el archivo local no existe."""
    raw_dir = tmp_path / "raw"
    manifest_dir = tmp_path / "manifests"
    raw_dir.mkdir()
    manifest_dir.mkdir()

    manifest_path = (
        manifest_dir
        / "20260101T000000000000Z_test_source.json"
    )
    write_test_manifest(
        manifest_path,
        source_id="test_source",
        status="success",
        file_size_bytes=10,
        sha256_hash="expected_hash",
    )

    source = {
        "source_id": "test_source",
        "resource_name": "missing.csv",
    }

    result = verify_source(
        source=source,
        raw_data_dir=raw_dir,
        manifest_dir=manifest_dir,
    )

    assert result["verified"] is False
    assert result["reason"] == "El archivo local no existe."


def test_verify_source_detects_hash_mismatch(
    tmp_path: Path,
) -> None:
    """Debe detectar un archivo modificado con igual tamaño."""
    raw_dir = tmp_path / "raw"
    manifest_dir = tmp_path / "manifests"
    raw_dir.mkdir()
    manifest_dir.mkdir()

    original_content = b"a,b\n1,2\n"
    modified_content = b"a,b\n9,9\n"

    source_file = raw_dir / "sample.csv"
    source_file.write_bytes(modified_content)

    original_hash = hashlib.sha256(
        original_content
    ).hexdigest()

    manifest_path = (
        manifest_dir
        / "20260101T000000000000Z_test_source.json"
    )
    write_test_manifest(
        manifest_path,
        source_id="test_source",
        status="success",
        file_size_bytes=len(original_content),
        sha256_hash=original_hash,
    )

    source = {
        "source_id": "test_source",
        "resource_name": "sample.csv",
    }

    result = verify_source(
        source=source,
        raw_data_dir=raw_dir,
        manifest_dir=manifest_dir,
        check_hash=True,
    )

    assert result["verified"] is False
    assert result["size_matches"] is True
    assert result["hash_matches"] is False