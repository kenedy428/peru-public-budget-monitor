# Peru Public Budget Monitor

Proyecto personal de portafolio orientado al análisis de la ejecución presupuestal pública del Perú mediante datos oficiales del Ministerio de Economía y Finanzas (MEF).

El objetivo es construir una solución analítica end-to-end que permita extraer, perfilar, validar, transformar, almacenar, analizar y visualizar datos de gasto público mediante un proceso reproducible y documentado.

## Estado del proyecto

> En desarrollo.

Actualmente, el proyecto se encuentra en su fase inicial de definición de alcance, preparación del repositorio y revisión de las fuentes oficiales de datos.

## Objetivo

Construir un pipeline analítico reproducible que transforme datos oficiales de ejecución presupuestal pública en información confiable y útil para:

- analizar la evolución temporal del monto devengado;
- comparar niveles de gobierno y entidades;
- identificar concentraciones y cambios abruptos;
- desarrollar KPIs reproducibles;
- visualizar resultados mediante Power BI;
- mantener trazabilidad, controles de calidad y documentación técnica.

El MVP permitirá analizar los años completos 2024 y 2025, así como el comportamiento de 2026 hasta el último periodo mensual disponible, utilizando comparaciones YTD para garantizar equivalencia temporal.

## Usuarios objetivo

La solución está dirigida principalmente a:

- analistas de presupuesto y planeamiento;
- equipos de control interno y auditoría;
- investigadores y periodistas de datos;
- ciudadanos interesados en el seguimiento del gasto público.

## Alcance inicial

El MVP contempla inicialmente:

- datos mensuales de ejecución presupuestal correspondientes a los años completos 2024 y 2025, así como a 2026 hasta el último periodo disponible;
- comparaciones YTD entre 2026 y periodos equivalentes de 2025 y 2024;
- extracción e ingesta mediante Python;
- perfilado y validación de calidad;
- transformación mediante pandas;
- almacenamiento en PostgreSQL;
- modelado dimensional;
- análisis mediante SQL;
- Análisis Exploratorio de Datos (EDA);
- KPIs y dashboard en Power BI;
- validación mediante Excel;
- pruebas, logs y documentación en GitHub.

El alcance podrá ajustarse después de inspeccionar el diccionario oficial y la estructura real de los datasets.

## Arquitectura propuesta

El flujo general previsto es:

```text
Fuente oficial MEF
        ↓
Extracción con Python
        ↓
Perfilado y controles de calidad
        ↓
Transformación con pandas
        ↓
PostgreSQL
        ↓
Modelo dimensional y SQL analítico
        ↓
EDA y KPIs
        ↓
Power BI y Excel QA
        ↓
Automatización y documentación

## Próximos pasos

1. Revisar las fuentes oficiales y el diccionario de datos.
2. Descargar y registrar los archivos fuente del MVP para 2024, 2025 y 2026.
3. Comparar los esquemas de los tres periodos antes de concatenar los datos.
4. Realizar el perfilado inicial.
5. Definir controles de calidad.
6. Construir el pipeline de transformación y carga.