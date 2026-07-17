"""Pruebas unitarias para el módulo de extracción."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from src.extract import (
    calculate_sha256,
    select_sources,
    validate_download,
)


def test_calculate_sha256(tmp_path: Path) -> None:
    """El hash calculado debe coincidir con el contenido del archivo."""
    file_path = tmp_path / "sample.txt"
    content = b"peru-public-budget-monitor"
    file_path.write_bytes(content)

    expected_hash = hashlib.sha256(content).hexdigest()

    assert calculate_sha256(file_path) == expected_hash


def test_validate_download_accepts_valid_csv(tmp_path: Path) -> None:
    """Un CSV no vacío y con tamaño correcto debe ser aceptado."""
    file_path = tmp_path / "sample.csv"
    content = b"column_a,column_b\n1,2\n"
    file_path.write_bytes(content)

    validate_download(
        file_path=file_path,
        expected_size=len(content),
        actual_size=len(content),
        file_format="csv",
    )


def test_validate_download_rejects_empty_file(tmp_path: Path) -> None:
    """Una descarga vacía debe generar un error."""
    file_path = tmp_path / "empty.csv"
    file_path.write_bytes(b"")

    with pytest.raises(ValueError, match="vacío"):
        validate_download(
            file_path=file_path,
            expected_size=0,
            actual_size=0,
            file_format="csv",
        )


def test_validate_download_rejects_incomplete_file(tmp_path: Path) -> None:
    """El tamaño recibido debe coincidir con Content-Length."""
    file_path = tmp_path / "incomplete.csv"
    content = b"a,b\n1,2\n"
    file_path.write_bytes(content)

    with pytest.raises(ValueError, match="incompleta"):
        validate_download(
            file_path=file_path,
            expected_size=len(content) + 10,
            actual_size=len(content),
            file_format="csv",
        )


def test_validate_download_rejects_html(tmp_path: Path) -> None:
    """Una página HTML no debe aceptarse como archivo CSV."""
    file_path = tmp_path / "response.csv"
    content = b"<!doctype html><html><body>Error</body></html>"
    file_path.write_bytes(content)

    with pytest.raises(ValueError, match="HTML"):
        validate_download(
            file_path=file_path,
            expected_size=len(content),
            actual_size=len(content),
            file_format="csv",
        )


def test_select_sources_uses_dictionary_by_default() -> None:
    """Sin argumentos debe seleccionarse el diccionario oficial."""
    config = {
        "sources": [
            {"source_id": "mef_devengado_2024"},
            {"source_id": "mef_devengado_dictionary"},
        ]
    }

    selected = select_sources(
        config=config,
        source_id=None,
        download_all=False,
    )

    assert len(selected) == 1
    assert selected[0]["source_id"] == "mef_devengado_dictionary"


def test_select_sources_returns_all_sources() -> None:
    """La opción --all debe devolver todas las fuentes configuradas."""
    sources = [
        {"source_id": "mef_devengado_2024"},
        {"source_id": "mef_devengado_dictionary"},
    ]
    config = {"sources": sources}

    selected = select_sources(
        config=config,
        source_id=None,
        download_all=True,
    )

    assert selected == sources


def test_select_sources_rejects_unknown_source() -> None:
    """Un source_id inexistente debe producir un mensaje claro."""
    config = {
        "sources": [
            {"source_id": "mef_devengado_dictionary"},
        ]
    }

    with pytest.raises(ValueError, match="No existe la fuente"):
        select_sources(
            config=config,
            source_id="unknown_source",
            download_all=False,
        )