"""Pruebas unitarias para la validación de calidad."""

from __future__ import annotations

from pathlib import Path

from src.validate_quality import (
    determine_reconciliation_status,
    identify_monetary_columns,
    validate_source_quality,
)


MONTH_COLUMNS = [
    "MONTO_DEVENGADO_ENERO",
    "MONTO_DEVENGADO_FEBRERO",
    "MONTO_DEVENGADO_MARZO",
    "MONTO_DEVENGADO_ABRIL",
    "MONTO_DEVENGADO_MAYO",
    "MONTO_DEVENGADO_JUNIO",
    "MONTO_DEVENGADO_JULIO",
    "MONTO_DEVENGADO_AGOSTO",
    "MONTO_DEVENGADO_SEPTIEMBRE",
    "MONTO_DEVENGADO_OCTUBRE",
    "MONTO_DEVENGADO_NOVIEMBRE",
    "MONTO_DEVENGADO_DICIEMBRE",
]


def build_header() -> str:
    """Construye la cabecera mínima requerida."""
    return ",".join(
        ["ANO_EJE", *MONTH_COLUMNS, "MONTO_DEVENGADO_ANUAL"]
    )

def test_identify_monetary_columns() -> None:
    """Debe identificar únicamente las columnas con prefijo MONTO_."""
    columns = [
        "ANO_EJE",
        "MONTO_PIA",
        "MONTO_PIM",
        "SECTOR",
        "MONTO_DEVENGADO_ANUAL",
    ]

    result = identify_monetary_columns(columns)

    assert result == [
        "MONTO_PIA",
        "MONTO_PIM",
        "MONTO_DEVENGADO_ANUAL",
    ]

def test_determine_reconciliation_status() -> None:
    """Debe clasificar resultados aprobados, advertidos y fallidos."""
    assert determine_reconciliation_status(0, 0) == "passed"
    assert determine_reconciliation_status(0, 1) == "warning"
    assert determine_reconciliation_status(1, 0) == "failed"


def test_validate_source_quality_accepts_valid_rows(
    tmp_path: Path,
) -> None:
    """Debe aprobar años y montos correctamente reconciliados."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    monthly_values = ["1"] * 12

    file_path = raw_dir / "sample.csv"
    file_path.write_text(
        (
            build_header()
            + "\n"
            + ",".join(["2026", *monthly_values, "12"])
            + "\n"
            + ",".join(["2026", *(["0"] * 12), "0"])
            + "\n"
        ),
        encoding="utf-8",
    )

    source = {
        "source_id": "test_source",
        "resource_name": "sample.csv",
        "reference_year": 2026,
        "encoding": "utf-8",
    }

    result = validate_source_quality(
        source=source,
        raw_data_dir=raw_dir,
        chunk_rows=1,
        reconciliation_tolerance=0.01,
    )

    assert result["row_count"] == 2
    assert result["year_validation"]["status"] == "passed"
    assert result["annual_reconciliation"]["status"] == "passed"
    assert result["annual_reconciliation"]["mismatch_count"] == 0


def test_validate_source_quality_detects_year_and_amount_mismatch(
    tmp_path: Path,
) -> None:
    """Debe detectar un año incorrecto y una suma anual diferente."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    monthly_values = ["1"] * 12

    file_path = raw_dir / "sample.csv"
    file_path.write_text(
        (
            build_header()
            + "\n"
            + ",".join(["2025", *monthly_values, "20"])
            + "\n"
        ),
        encoding="utf-8",
    )

    source = {
        "source_id": "test_source",
        "resource_name": "sample.csv",
        "reference_year": 2026,
        "encoding": "utf-8",
    }

    result = validate_source_quality(
        source=source,
        raw_data_dir=raw_dir,
        chunk_rows=10,
        reconciliation_tolerance=0.01,
    )

    assert result["year_validation"]["status"] == "failed"
    assert result["year_validation"]["mismatch_count"] == 1
    assert result["annual_reconciliation"]["status"] == "failed"
    assert result["annual_reconciliation"]["mismatch_count"] == 1


def test_validate_source_quality_warns_when_amount_is_missing(
    tmp_path: Path,
) -> None:
    """Una fila incompleta no debe reconciliarse silenciosamente."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    monthly_values = ["1"] * 11 + [""]

    file_path = raw_dir / "sample.csv"
    file_path.write_text(
        (
            build_header()
            + "\n"
            + ",".join(["2026", *monthly_values, "11"])
            + "\n"
        ),
        encoding="utf-8",
    )

    source = {
        "source_id": "test_source",
        "resource_name": "sample.csv",
        "reference_year": 2026,
        "encoding": "utf-8",
    }

    result = validate_source_quality(
        source=source,
        raw_data_dir=raw_dir,
        chunk_rows=10,
        reconciliation_tolerance=0.01,
    )

    assert result["annual_reconciliation"]["status"] == "warning"
    assert (
        result["annual_reconciliation"]["not_evaluated_count"]
        == 1
    )
    assert result["columns_with_nulls_count"] == 1

def test_validate_source_quality_detects_negative_amounts(
    tmp_path: Path,
) -> None:
    """Debe registrar montos negativos como advertencia."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    monthly_values = [
        "-1",
        "1",
        *(["0"] * 10),
    ]

    file_path = raw_dir / "sample.csv"
    file_path.write_text(
        (
            build_header()
            + "\n"
            + ",".join(["2026", *monthly_values, "0"])
            + "\n"
        ),
        encoding="utf-8",
    )

    source = {
        "source_id": "test_source",
        "resource_name": "sample.csv",
        "reference_year": 2026,
        "encoding": "utf-8",
    }

    result = validate_source_quality(
        source=source,
        raw_data_dir=raw_dir,
        chunk_rows=10,
        reconciliation_tolerance=0.01,
    )

    assert result["annual_reconciliation"]["status"] == "passed"
    assert result["negative_amounts"]["status"] == "warning"
    assert result["negative_amounts"][
        "total_negative_amount_count"
    ] == 1
    assert result["negative_amounts"][
        "columns_with_negative_amounts"
    ] == ["MONTO_DEVENGADO_ENERO"]

def test_validate_source_quality_detects_whitespace_only_values(
    tmp_path: Path,
) -> None:
    """Debe detectar cadenas formadas únicamente por espacios."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    monthly_values = ["1"] * 12

    file_path = raw_dir / "sample.csv"
    file_path.write_text(
        (
            "META_NOMBRE,"
            + build_header()
            + "\n"
            + ",".join(
                [
                    "   ",
                    "2026",
                    *monthly_values,
                    "12",
                ]
            )
            + "\n"
        ),
        encoding="utf-8",
    )

    source = {
        "source_id": "test_source",
        "resource_name": "sample.csv",
        "reference_year": 2026,
        "encoding": "utf-8",
    }

    result = validate_source_quality(
        source=source,
        raw_data_dir=raw_dir,
        chunk_rows=10,
        reconciliation_tolerance=0.01,
    )

    blank_like = result["blank_like_values"]

    assert blank_like["status"] == "warning"
    assert blank_like["total_blank_like_count"] == 1
    assert blank_like["blank_like_counts"]["META_NOMBRE"] == 1
    assert result["null_counts"]["META_NOMBRE"] == 0

def test_validate_source_quality_classifies_structural_blanks(
    tmp_path: Path,
) -> None:
    """Los vacíos de sector y pliego local deben ser informativos."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    monthly_values = ["1"] * 12

    file_path = raw_dir / "sample.csv"
    file_path.write_text(
        (
            "NIVEL_GOBIERNO_NOMBRE,"
            "SECTOR,SECTOR_NOMBRE,"
            "PLIEGO,PLIEGO_NOMBRE,"
            + build_header()
            + "\n"
            + ",".join(
                [
                    "GOBIERNOS LOCALES",
                    "   ",
                    "   ",
                    "   ",
                    "   ",
                    "2026",
                    *monthly_values,
                    "12",
                ]
            )
            + "\n"
        ),
        encoding="utf-8",
    )

    source = {
        "source_id": "test_source",
        "resource_name": "sample.csv",
        "reference_year": 2026,
        "encoding": "utf-8",
    }

    result = validate_source_quality(
        source=source,
        raw_data_dir=raw_dir,
        chunk_rows=10,
        reconciliation_tolerance=0.01,
    )

    blank_like = result["blank_like_values"]

    assert blank_like["status"] == "informational"
    assert blank_like["total_blank_like_count"] == 4
    assert blank_like["total_structural_blank_like_count"] == 4
    assert blank_like["total_unexpected_blank_like_count"] == 0
    assert result["quality_summary"]["warnings"] == 0
    assert (
        result["quality_summary"]["informational_findings"]
        == 1
    )

def test_validate_source_quality_reports_structural_and_unexpected_blanks(
    tmp_path: Path,
) -> None:
    """Debe reportar a la vez vacíos estructurales e inesperados."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    monthly_values = ["1"] * 12

    file_path = raw_dir / "sample.csv"
    file_path.write_text(
        (
            "NIVEL_GOBIERNO_NOMBRE,"
            "SECTOR,SECTOR_NOMBRE,"
            "PLIEGO,PLIEGO_NOMBRE,"
            "META_NOMBRE,"
            + build_header()
            + "\n"
            + ",".join(
                [
                    "GOBIERNOS LOCALES",
                    "   ",
                    "   ",
                    "   ",
                    "   ",
                    "   ",
                    "2026",
                    *monthly_values,
                    "12",
                ]
            )
            + "\n"
        ),
        encoding="utf-8",
    )

    source = {
        "source_id": "test_source",
        "resource_name": "sample.csv",
        "reference_year": 2026,
        "encoding": "utf-8",
    }

    result = validate_source_quality(
        source=source,
        raw_data_dir=raw_dir,
        chunk_rows=10,
        reconciliation_tolerance=0.01,
    )

    blank_like = result["blank_like_values"]

    assert blank_like["status"] == "warning"
    assert blank_like["total_structural_blank_like_count"] == 4
    assert blank_like["total_unexpected_blank_like_count"] == 1
    assert result["quality_summary"]["warnings"] == 1
    assert (
        result["quality_summary"]["informational_findings"]
        == 1
    )