"""Revisión reproducible del diccionario oficial del MEF."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DICTIONARY_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "Gasto_Devengado_Diccionario.csv"
)

MANIFEST_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "manifests"
)

STAGING_SQL_PATH = (
    PROJECT_ROOT
    / "sql"
    / "002_create_staging_table.sql"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "docs"
    / "data_dictionary_review.md"
)

EXPECTED_DICTIONARY_COLUMNS = [
    "VARIABLE",
    "TIPO_DATO",
    "DESCRIPCION",
]


def calculate_sha256(path: Path) -> str:
    """Calcula el SHA-256 de un archivo."""
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def read_dictionary() -> list[dict[str, str]]:
    """Lee y valida el diccionario oficial."""
    if not DICTIONARY_PATH.exists():
        raise FileNotFoundError(
            f"No existe {DICTIONARY_PATH}."
        )

    with DICTIONARY_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        if reader.fieldnames != EXPECTED_DICTIONARY_COLUMNS:
            raise ValueError(
                "Encabezado inesperado en el diccionario: "
                f"{reader.fieldnames!r}"
            )

        rows = [
            {
                key: (value or "").strip()
                for key, value in row.items()
            }
            for row in reader
        ]

    if not rows:
        raise ValueError(
            "El diccionario no contiene registros."
        )

    variables = [
        row["VARIABLE"]
        for row in rows
    ]

    duplicate_variables = sorted(
        {
            variable
            for variable in variables
            if variables.count(variable) > 1
        }
    )

    if duplicate_variables:
        raise ValueError(
            "Variables duplicadas en el diccionario: "
            f"{duplicate_variables}"
        )

    return rows


def read_staging_columns() -> list[str]:
    """Extrae las columnas de la tabla staging versionada."""
    sql = STAGING_SQL_PATH.read_text(
        encoding="utf-8"
    )

    match = re.search(
        (
            r"CREATE TABLE IF NOT EXISTS\s+"
            r"staging\.mef_devengado\s*\("
            r"(?P<body>.*?)"
            r"\n\);"
        ),
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if match is None:
        raise ValueError(
            "No se encontró la definición de "
            "staging.mef_devengado."
        )

    columns: list[str] = []

    for line in match.group("body").splitlines():
        definition = line.strip().rstrip(",")

        if not definition or definition.startswith("--"):
            continue

        columns.append(
            definition.split()[0].lower()
        )

    return columns


def read_latest_manifest() -> tuple[Path, dict[str, Any]]:
    """Obtiene el manifiesto más reciente del diccionario."""
    manifest_paths = list(
        MANIFEST_DIRECTORY.glob(
            "*_mef_devengado_dictionary.json"
        )
    )

    if not manifest_paths:
        raise FileNotFoundError(
            "No existen manifiestos del diccionario."
        )

    latest_manifest_path = max(
        manifest_paths,
        key=lambda path: path.stat().st_mtime,
    )

    manifest = json.loads(
        latest_manifest_path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(manifest, dict):
        raise ValueError(
            "El manifiesto debe ser un objeto JSON."
        )

    return latest_manifest_path, manifest


def escape_markdown(value: object) -> str:
    """Escapa contenido para una tabla Markdown."""
    return (
        str(value)
        .replace("|", r"\|")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def build_report() -> str:
    """Construye la revisión documentada."""
    dictionary_rows = read_dictionary()
    staging_columns = read_staging_columns()

    (
        latest_manifest_path,
        manifest,
    ) = read_latest_manifest()

    dictionary_variables = [
        row["VARIABLE"]
        for row in dictionary_rows
    ]

    dictionary_columns = {
        variable.lower()
        for variable in dictionary_variables
    }

    staging_column_set = set(
        staging_columns
    )

    missing_in_staging = sorted(
        dictionary_columns
        - staging_column_set
    )

    undocumented_in_dictionary = sorted(
        staging_column_set
        - dictionary_columns
    )

    actual_sha256 = calculate_sha256(
        DICTIONARY_PATH
    )

    manifest_sha256 = str(
        manifest.get("sha256_hash", "")
    )

    hash_matches = (
        actual_sha256 == manifest_sha256
    )

    exact_schema_match = (
        not missing_in_staging
        and not undocumented_in_dictionary
        and len(dictionary_rows)
        == len(staging_columns)
    )

    lines = [
        "# Revisión del diccionario de datos del MEF",
        "",
        "## 1. Fuente revisada",
        "",
        "| Campo | Valor |",
        "|---|---|",
        (
            "| Archivo | "
            f"`{DICTIONARY_PATH.relative_to(PROJECT_ROOT)}` |"
        ),
        (
            "| Manifiesto | "
            f"`{latest_manifest_path.relative_to(PROJECT_ROOT)}` |"
        ),
        (
            "| Recurso | "
            f"{escape_markdown(manifest.get('resource_name', ''))} |"
        ),
        (
            "| URL de origen | "
            f"{escape_markdown(manifest.get('source_url', ''))} |"
        ),
        (
            "| Fecha de descarga UTC | "
            f"{escape_markdown(manifest.get('download_timestamp_utc', ''))} |"
        ),
        (
            "| Codificación | "
            f"`{escape_markdown(manifest.get('configured_encoding', ''))}` |"
        ),
        (
            "| SHA-256 del manifiesto | "
            f"`{manifest_sha256}` |"
        ),
        (
            "| SHA-256 calculado | "
            f"`{actual_sha256}` |"
        ),
        (
            "| Hash coincidente | "
            f"{'Sí' if hash_matches else 'No'} |"
        ),
        (
            "| Fuente mutable | "
            f"{escape_markdown(manifest.get('mutable_source', ''))} |"
        ),
        "",
        "## 2. Validación estructural",
        "",
        "| Control | Resultado |",
        "|---|---:|",
        (
            "| Registros del diccionario | "
            f"{len(dictionary_rows)} |"
        ),
        (
            "| Columnas en staging | "
            f"{len(staging_columns)} |"
        ),
        (
            "| Variables duplicadas | 0 |"
        ),
        (
            "| Coincidencia exacta con staging | "
            f"{'Sí' if exact_schema_match else 'No'} |"
        ),
        "",
        "### Variables del diccionario ausentes en staging",
        "",
        (
            ", ".join(
                f"`{column}`"
                for column in missing_in_staging
            )
            if missing_in_staging
            else "Ninguna."
        ),
        "",
        "### Columnas staging no documentadas",
        "",
        (
            ", ".join(
                f"`{column}`"
                for column in undocumented_in_dictionary
            )
            if undocumented_in_dictionary
            else "Ninguna."
        ),
        "",
        "## 3. Alcance del diccionario",
        "",
        (
            "El diccionario proporciona el nombre técnico, "
            "el tipo general y la descripción oficial de cada "
            "variable."
        ),
        "",
        (
            "No contiene campos específicos para declarar "
            "claves primarias, cardinalidades, dependencias "
            "jerárquicas o vigencia histórica. Estos aspectos "
            "deben validarse posteriormente sobre los datos."
        ),
        "",
        "## 4. Definiciones oficiales",
        "",
        "| N.º | Variable | Tipo de dato | Descripción |",
        "|---:|---|---|---|",
    ]

    for position, row in enumerate(
        dictionary_rows,
        start=1,
    ):
        lines.append(
            "| "
            f"{position} | "
            f"`{escape_markdown(row['VARIABLE'])}` | "
            f"{escape_markdown(row['TIPO_DATO'])} | "
            f"{escape_markdown(row['DESCRIPCION'])} |"
        )

    lines.extend(
        [
            "",
            "## 5. Conclusión de esta revisión",
            "",
            (
                "Las definiciones del diccionario se utilizarán "
                "para interpretar las variables y formular "
                "hipótesis de modelado."
            ),
            "",
            (
                "Las claves naturales, relaciones y jerarquías "
                "solo se aceptarán después de validarlas con los "
                "datos reales almacenados en PostgreSQL."
            ),
            "",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    """Ejecuta la revisión y genera el documento."""
    try:
        report = build_report()

        OUTPUT_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        OUTPUT_PATH.write_text(
            report,
            encoding="utf-8",
        )

        print(
            "Documento generado:",
            OUTPUT_PATH.relative_to(PROJECT_ROOT),
        )

        print(
            "Revisión completada correctamente."
        )

        return 0

    except Exception as error:
        print(
            f"La revisión falló: {error}",
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    sys.exit(main())