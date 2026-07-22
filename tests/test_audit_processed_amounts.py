"""Pruebas de la auditoría monetaria exacta."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.audit_processed_amounts import (
    audit_processed_csv,
    parse_amount_to_cents,
)


def test_parse_amount_to_cents_handles_exact_values() -> None:
    """Debe convertir importes exactos a centavos."""
    assert parse_amount_to_cents("123") == (
        12_300,
        False,
        False,
    )

    assert parse_amount_to_cents("1.2") == (
        120,
        False,
        False,
    )

    assert parse_amount_to_cents("1.2300") == (
        123,
        True,
        False,
    )

    assert parse_amount_to_cents("") == (
        0,
        False,
        False,
    )


def test_parse_amount_to_cents_rounds_half_up() -> None:
    """Debe aplicar el mismo redondeo monetario esperado."""
    assert parse_amount_to_cents("1.234") == (
        123,
        True,
        True,
    )

    assert parse_amount_to_cents("1.235") == (
        124,
        True,
        True,
    )

    assert parse_amount_to_cents("-1.235") == (
        -124,
        True,
        True,
    )

    assert parse_amount_to_cents(
        "0.30000000000000004"
    ) == (
        30,
        True,
        True,
    )


def test_parse_amount_to_cents_rejects_invalid_values() -> None:
    """Debe rechazar importes que no sean numéricos."""
    with pytest.raises(
        ValueError,
        match="Importe monetario inválido",
    ):
        parse_amount_to_cents(
            "no-numérico"
        )


def test_audit_processed_csv_calculates_exact_totals(
    tmp_path: Path,
) -> None:
    """Debe sumar centavos y registrar los redondeos."""
    source_path = tmp_path / "sample.csv"

    source_path.write_text(
        (
            "KEY,MONTO_PIA,MONTO_PIM\n"
            "A,1.234,0.30000000000000004\n"
            "B,2.00,\n"
        ),
        encoding="utf-8",
    )

    report = audit_processed_csv(
        source_file_path=source_path,
        source_id="test_source",
        expected_amount_column_count=2,
    )

    assert report["row_count"] == 2
    assert report["amount_column_count"] == 2

    assert report["exact_amount_totals"] == {
        "MONTO_PIA": "3.23",
        "MONTO_PIM": "0.30",
    }

    assert (
        report[
            "total_values_with_extra_decimal_digits"
        ]
        == 2
    )

    assert (
        report[
            "total_values_requiring_rounding"
        ]
        == 2
    )