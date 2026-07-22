"""Auditoría monetaria exacta de los CSV procesados."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from datetime import UTC, datetime
from decimal import (
    Decimal,
    InvalidOperation,
    ROUND_HALF_UP,
)
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROGRESS_ROW_INTERVAL = 250_000
CENT = Decimal("0.01")


def configure_logging() -> None:
    """Configura los mensajes de avance."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def format_cents(cents: int) -> str:
    """Convierte centavos enteros a una cadena monetaria."""
    sign = "-" if cents < 0 else ""
    absolute_cents = abs(cents)
    whole, fraction = divmod(absolute_cents, 100)

    return f"{sign}{whole}.{fraction:02d}"


def parse_amount_to_cents(
    value: str,
) -> tuple[int, bool, bool]:
    """Convierte un importe a centavos con redondeo HALF_UP.

    Retorna:
        centavos,
        si el texto tenía más de dos dígitos decimales,
        si el valor necesitó un redondeo monetario.
    """
    text = value.strip()

    if not text:
        return 0, False, False

    sign = 1

    if text[0] in {"+", "-"}:
        if text[0] == "-":
            sign = -1

        text = text[1:]

    if not text:
        raise ValueError(
            f"Importe monetario inválido: {value!r}"
        )

    if "e" in text.lower():
        return parse_decimal_fallback(
            original_value=value,
        )

    whole, separator, fraction = text.partition(".")

    if not whole:
        whole = "0"

    valid_fraction = (
        not fraction
        or fraction.isdigit()
    )

    if (
        not whole.isdigit()
        or not valid_fraction
        or (separator and "." in fraction)
    ):
        return parse_decimal_fallback(
            original_value=value,
        )

    has_extra_decimal_digits = len(fraction) > 2

    requires_rounding = any(
        digit != "0"
        for digit in fraction[2:]
    )

    padded_fraction = fraction + "000"

    fractional_cents = int(
        padded_fraction[:2]
    )

    third_decimal_digit = int(
        padded_fraction[2]
    )

    if third_decimal_digit >= 5:
        fractional_cents += 1

    cents = (
        int(whole) * 100
        + fractional_cents
    )

    return (
        sign * cents,
        has_extra_decimal_digits,
        requires_rounding,
    )


def parse_decimal_fallback(
    original_value: str,
) -> tuple[int, bool, bool]:
    """Procesa notación científica u otros decimales válidos."""
    try:
        amount = Decimal(
            original_value.strip()
        )
    except InvalidOperation as error:
        raise ValueError(
            "Importe monetario inválido: "
            f"{original_value!r}"
        ) from error

    if not amount.is_finite():
        raise ValueError(
            "El importe monetario debe ser finito: "
            f"{original_value!r}"
        )

    rounded_amount = amount.quantize(
        CENT,
        rounding=ROUND_HALF_UP,
    )

    decimal_places = max(
        -amount.as_tuple().exponent,
        0,
    )

    cents = int(
        rounded_amount * 100
    )

    return (
        cents,
        decimal_places > 2,
        amount != rounded_amount,
    )


def audit_processed_csv(
    source_file_path: Path,
    source_id: str,
    sample_limit: int = 5,
    expected_amount_column_count: int = 18,
) -> dict[str, Any]:
    """Audita los importes de un CSV sin usar punto flotante."""
    source_file_path = Path(
        source_file_path
    )

    if not source_file_path.exists():
        raise FileNotFoundError(
            f"No existe el archivo: {source_file_path}"
        )

    if sample_limit < 0:
        raise ValueError(
            "sample_limit no puede ser negativo."
        )

    with source_file_path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as source_file:
        reader = csv.reader(source_file)

        try:
            header = next(reader)
        except StopIteration as error:
            raise ValueError(
                "El archivo procesado está vacío."
            ) from error

        amount_columns = [
            column
            for column in header
            if column.startswith("MONTO_")
        ]

        if (
            len(amount_columns)
            != expected_amount_column_count
        ):
            raise ValueError(
                "Cantidad inesperada de columnas monetarias: "
                f"{len(amount_columns)}; se esperaban "
                f"{expected_amount_column_count}."
            )

        column_indexes = {
            column: header.index(column)
            for column in amount_columns
        }

        totals_in_cents = {
            column: 0
            for column in amount_columns
        }

        extra_decimal_counts = {
            column: 0
            for column in amount_columns
        }

        rounding_counts = {
            column: 0
            for column in amount_columns
        }

        rounding_samples = {
            column: []
            for column in amount_columns
        }

        row_count = 0

        for row_number, row in enumerate(
            reader,
            start=2,
        ):
            if len(row) != len(header):
                raise ValueError(
                    f"Fila {row_number} malformada: "
                    f"{len(row)} valores; se esperaban "
                    f"{len(header)}."
                )

            row_count += 1

            for column in amount_columns:
                raw_value = row[
                    column_indexes[column]
                ]

                try:
                    (
                        cents,
                        has_extra_decimals,
                        requires_rounding,
                    ) = parse_amount_to_cents(
                        raw_value
                    )
                except ValueError as error:
                    raise ValueError(
                        f"Fila {row_number}, "
                        f"columna {column}: {error}"
                    ) from error

                totals_in_cents[column] += cents

                if has_extra_decimals:
                    extra_decimal_counts[column] += 1

                if requires_rounding:
                    rounding_counts[column] += 1

                    if (
                        len(rounding_samples[column])
                        < sample_limit
                    ):
                        rounding_samples[column].append(
                            {
                                "row_number": row_number,
                                "raw_value": raw_value,
                                "rounded_value": (
                                    format_cents(cents)
                                ),
                            }
                        )

            if (
                row_count
                % PROGRESS_ROW_INTERVAL
                == 0
            ):
                logging.info(
                    "%s | filas auditadas=%s",
                    source_id,
                    f"{row_count:,}",
                )

    total_extra_decimal_values = sum(
        extra_decimal_counts.values()
    )

    total_values_requiring_rounding = sum(
        rounding_counts.values()
    )

    return {
        "source_id": source_id,
        "source_file_path": str(
            source_file_path
        ),
        "row_count": row_count,
        "amount_column_count": len(
            amount_columns
        ),
        "totals_in_cents": (
            totals_in_cents
        ),
        "exact_amount_totals": {
            column: format_cents(cents)
            for column, cents
            in totals_in_cents.items()
        },
        "values_with_extra_decimal_digits": (
            extra_decimal_counts
        ),
        "values_requiring_rounding": (
            rounding_counts
        ),
        "total_values_with_extra_decimal_digits": (
            total_extra_decimal_values
        ),
        "total_values_requiring_rounding": (
            total_values_requiring_rounding
        ),
        "rounding_samples": {
            column: samples
            for column, samples
            in rounding_samples.items()
            if samples
        },
        "rounding_mode": "ROUND_HALF_UP",
        "target_decimal_places": 2,
        "audited_at_utc": (
            datetime.now(UTC).isoformat()
        ),
    }


def write_audit_report(
    report: dict[str, Any],
    processed_dir: Path,
) -> Path:
    """Guarda el resultado exacto en JSON."""
    timestamp = datetime.now(UTC).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )

    report_path = (
        processed_dir
        / (
            f"{timestamp}_{report['source_id']}"
            "_exact_amount_audit.json"
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
    """Define la interfaz de consola."""
    parser = argparse.ArgumentParser(
        description=(
            "Audita los montos de un CSV procesado "
            "usando centavos enteros."
        )
    )

    parser.add_argument(
        "--source-id",
        required=True,
        help=(
            "Identificador como "
            "mef_devengado_2026."
        ),
    )

    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=DEFAULT_PROCESSED_DIR,
        help="Directorio de datos procesados.",
    )

    parser.add_argument(
        "--sample-limit",
        type=int,
        default=5,
        help=(
            "Máximo de muestras de redondeo "
            "por columna."
        ),
    )

    return parser.parse_args()


def main() -> int:
    """Ejecuta la auditoría monetaria."""
    configure_logging()
    args = parse_arguments()

    try:
        processed_dir = (
            args.processed_dir.resolve()
        )

        source_file_path = (
            processed_dir
            / f"{args.source_id}_consolidated.csv"
        )

        report = audit_processed_csv(
            source_file_path=source_file_path,
            source_id=args.source_id,
            sample_limit=args.sample_limit,
        )

        report_path = write_audit_report(
            report=report,
            processed_dir=processed_dir,
        )

        logging.info(
            "%s | filas=%s | "
            "valores con más de dos decimales=%s | "
            "valores que requieren redondeo=%s",
            report["source_id"],
            f"{report['row_count']:,}",
            f"{report[
                'total_values_with_extra_decimal_digits'
            ]:,}",
            f"{report[
                'total_values_requiring_rounding'
            ]:,}",
        )

        logging.info(
            "Reporte generado: %s",
            report_path,
        )

        return 0

    except Exception as error:
        logging.exception(
            "La auditoría monetaria falló: %s",
            error,
        )

        return 1


if __name__ == "__main__":
    sys.exit(main())