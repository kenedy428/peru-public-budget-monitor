# ADR 001: Estrategia de acceso a los datos del MEF

## Estado

Aceptada.

## Fecha

16 de julio de 2026.

## Contexto

El Portal de Datos Abiertos del MEF ofrece dos mecanismos para acceder a los recursos seleccionados:

1. Descarga directa de archivos CSV.
2. API oficial de datos basada en CKAN.

Los archivos anuales del proyecto contienen más de dos millones de registros, por lo que se necesita un mecanismo reproducible que permita recuperar el contenido completo de manera eficiente.

Se realizó una prueba comparativa con el diccionario oficial de datos, que contiene 73 registros.

## Decisión

Se utilizará la descarga directa de archivos CSV como mecanismo principal de ingesta.

La API se utilizará como mecanismo complementario para:

- consultas filtradas;
- validaciones puntuales;
- obtención de muestras;
- comprobaciones de registros;
- pruebas de disponibilidad del recurso.

## Justificación

La descarga directa:

- recupera el archivo completo en una sola operación;
- genera menor sobrecarga que JSON;
- simplifica el cálculo de tamaño y hash;
- resulta más adecuada para recursos con millones de registros.

La API:

- permite aplicar filtros y consultas;
- devuelve resultados estructurados;
- requiere manejar paginación;
- genera una respuesta más pesada por registro;
- no resulta conveniente como mecanismo principal para descargar millones de filas.

## Consecuencias

- El pipeline deberá admitir URLs directas configurables.
- Cada descarga registrará timestamp, tamaño y hash SHA-256.
- En Windows podrá ser necesario utilizar `--ssl-revoke-best-effort`.
- Los CSV deberán inspeccionarse para detectar BOM y codificación.
- La API permanecerá disponible como herramienta de validación.