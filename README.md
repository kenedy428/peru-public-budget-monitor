# Peru Public Budget Monitor

Proyecto personal de portafolio orientado al análisis de la ejecución presupuestal pública del Perú mediante datos oficiales del Ministerio de Economía y Finanzas (MEF).

El objetivo es construir una solución analítica end-to-end que permita extraer, validar, transformar, almacenar, analizar y visualizar datos de gasto público mediante un proceso reproducible, trazable y documentado.

## Estado del proyecto

> En desarrollo.

Actualmente, el proyecto cuenta con:

- definición del problema, usuarios objetivo y alcance del MVP;
- investigación documentada de las fuentes oficiales del MEF;
- configuración centralizada de los recursos 2024, 2025, 2026 y el diccionario de datos;
- descarga reproducible de archivos mediante Python;
- generación de manifiestos con metadatos y hashes SHA-256;
- manejo de fuentes mutables y comparación de versiones;
- reintentos automáticos ante errores temporales de red;
- verificación de existencia, tamaño e integridad de los archivos;
- pruebas unitarias automatizadas para los módulos de ingesta y verificación.

La siguiente etapa corresponde al perfilado estructural y de calidad de los datasets descargados.

## Objetivo

Construir un pipeline analítico reproducible que transforme datos oficiales de ejecución presupuestal pública en información confiable y útil para:

- analizar la evolución temporal del monto devengado;
- comparar niveles de gobierno, territorios y entidades;
- identificar concentraciones, variaciones y cambios abruptos;
- desarrollar KPIs reproducibles;
- visualizar resultados mediante Power BI;
- mantener trazabilidad entre las fuentes, transformaciones y resultados;
- implementar controles de calidad y validaciones automatizadas.

El MVP permitirá analizar los años completos 2024 y 2025, así como el comportamiento de 2026 hasta el último periodo mensual disponible.

Las comparaciones que involucren 2026 se realizarán mediante periodos equivalentes YTD para evitar comparar un año en curso contra años completos.

## Usuarios objetivo

La solución está dirigida principalmente a:

- analistas de presupuesto y planeamiento;
- equipos de control interno y auditoría;
- investigadores y periodistas de datos;
- ciudadanos interesados en el seguimiento del gasto público;
- reclutadores técnicos interesados en verificar competencias de Data Analytics, Python, SQL, Business Intelligence y Data Engineering.

## Alcance del MVP

El MVP contempla:

- datos mensuales de ejecución presupuestal de 2024 y 2025;
- datos de 2026 hasta el último periodo mensual disponible;
- comparaciones YTD entre 2026 y periodos equivalentes de 2025 y 2024;
- ingesta reproducible mediante Python;
- registro de metadatos y hashes SHA-256;
- perfilado y validación de calidad;
- transformación mediante pandas;
- almacenamiento relacional en PostgreSQL;
- modelado dimensional;
- análisis mediante SQL;
- Análisis Exploratorio de Datos (EDA);
- definición de KPIs;
- dashboard en Power BI;
- validaciones mediante Excel;
- pruebas automatizadas;
- documentación técnica y funcional en GitHub.

El alcance podrá ajustarse después de completar el perfilado del diccionario oficial y de los archivos correspondientes a cada periodo.

## Arquitectura propuesta

El flujo general previsto es:

```text
Fuente oficial MEF
        ↓
Configuración de fuentes
        ↓
Extracción reproducible con Python
        ↓
Registro de metadatos y hashes
        ↓
Verificación de integridad
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
```

La arquitectura podrá modificarse de acuerdo con las características reales de los datos y las decisiones técnicas documentadas durante el desarrollo.

## Fuentes de datos

La fuente principal es el conjunto oficial:

**Presupuesto y Ejecución de Gasto – Devengado Mensual**

Publicado por el Ministerio de Economía y Finanzas del Perú.

El MVP utiliza los siguientes recursos:

| Periodo | Recurso |
|---|---|
| 2024 | `2024-Gasto-Devengado.csv` |
| 2025 | `2025-Gasto-Devengado-Mensual.csv` |
| 2026 | `2026-Gasto-Devengado-Mensual.csv` |
| Diccionario | `Gasto_Devengado_Diccionario.csv` |

Los archivos originales no se versionan en GitHub debido a su tamaño. Pueden reproducirse mediante el proceso de ingesta documentado en el repositorio.

## Stack tecnológico

### Implementado

- Python 3.12
- requests
- PyYAML
- pytest
- Git
- GitHub

### Previsto para las siguientes etapas

- pandas
- Jupyter Notebook
- PostgreSQL
- SQL
- Power BI
- Excel

Las herramientas se incorporan únicamente cuando tienen una responsabilidad concreta dentro de la solución.

## Funcionalidades implementadas

### Configuración de fuentes

Las URLs, Resource IDs, nombres de archivos, codificaciones y condiciones de mutabilidad se encuentran centralizadas en:

```text
config/sources.yaml
```

### Ingesta reproducible

El módulo:

```text
src/extract.py
```

permite:

- descargar una fuente específica o todos los recursos;
- descargar los archivos por bloques sin cargarlos completamente en memoria;
- utilizar archivos temporales `.part`;
- validar respuestas vacías, incompletas o HTML;
- calcular hashes SHA-256;
- registrar manifiestos JSON;
- manejar fuentes mutables;
- comparar versiones anteriores y actuales;
- aplicar reintentos ante errores HTTP temporales;
- registrar manifiestos de error cuando una descarga falla.

### Verificación de integridad

El módulo:

```text
src/verify_sources.py
```

permite comprobar:

- existencia del archivo local;
- coincidencia del tamaño;
- coincidencia del hash SHA-256;
- validez del manifiesto más reciente;
- posibles modificaciones o daños posteriores a la descarga.

### Pruebas automatizadas

Las pruebas se encuentran en:

```text
tests/
```

Actualmente validan:

- cálculo de SHA-256;
- detección de archivos vacíos;
- detección de descargas incompletas;
- rechazo de respuestas HTML;
- selección de fuentes;
- configuración de reintentos HTTP;
- tratamiento de fuentes mutables;
- clasificación de estados;
- selección del manifiesto más reciente;
- detección de archivos ausentes;
- detección de modificaciones mediante hash.

## Estructura actual del repositorio

```text
peru-public-budget-monitor/
├── config/
│   └── sources.yaml
├── data/
│   ├── manifests/
│   │   └── README.md
│   └── raw/
│       └── README.md
├── docs/
│   ├── decisions/
│   │   └── 001-data-access-strategy.md
│   ├── data_sources.md
│   ├── ingestion.md
│   └── project_scope.md
├── src/
│   ├── __init__.py
│   ├── extract.py
│   └── verify_sources.py
├── tests/
│   ├── test_extract.py
│   └── test_verify_sources.py
├── .gitignore
├── README.md
└── requirements.txt
```

Los archivos descargados y los manifiestos generados se mantienen localmente y están excluidos mediante `.gitignore`.

## Ejecución

### Crear el entorno virtual

```bash
py -3.12 -m venv .venv
```

### Activar el entorno en Git Bash

```bash
source .venv/Scripts/activate
```

### Instalar dependencias

```bash
python -m pip install -r requirements.txt
```

### Descargar todas las fuentes

```bash
python -m src.extract --all
```

### Verificar rápidamente los archivos

```bash
python -m src.verify_sources --quick
```

### Verificar tamaño y hash

```bash
python -m src.verify_sources
```

### Ejecutar las pruebas

```bash
python -m pytest -v
```

Las instrucciones completas se encuentran en `docs/ingestion.md`.

## Estados de ingesta

Los manifiestos pueden registrar los siguientes estados:

| Estado | Significado |
|---|---|
| `success` | El archivo no existía y fue descargado correctamente |
| `updated` | El archivo existía y la versión oficial cambió |
| `unchanged` | La fuente mutable fue revisada y su contenido no cambió |
| `refreshed` | La descarga fue forzada, aunque el contenido era idéntico |
| `skipped_existing` | Se conservó una fuente inmutable ya existente |
| `failed` | La descarga no pudo completarse |

## Documentación

La definición del problema, los usuarios objetivo, las preguntas de negocio y el alcance del MVP se encuentran en:

- `docs/project_scope.md`

La investigación de las fuentes oficiales del MEF se encuentra en:

- `docs/data_sources.md`

La decisión técnica sobre el uso de descarga directa y API se encuentra en:

- `docs/decisions/001-data-access-strategy.md`

Las instrucciones para preparar el entorno, descargar las fuentes y verificar su integridad se encuentran en:

- `docs/ingestion.md`

## Principios del proyecto

- No inventar variables que no existan en la fuente oficial.
- No definir KPIs definitivos antes de revisar el diccionario y las columnas reales.
- No confundir monto devengado con porcentaje de ejecución presupuestal.
- No comparar un año incompleto contra años completos.
- No presentar patrones atípicos como evidencia de corrupción, irregularidad o ineficiencia.
- Mantener trazabilidad entre la fuente, las transformaciones y los resultados.
- No versionar credenciales, secretos ni datasets masivos.
- Documentar decisiones técnicas, limitaciones y supuestos.
- Priorizar reproducibilidad y calidad antes que complejidad innecesaria.

## Próximos pasos

1. Realizar el perfilado inicial de los archivos 2024, 2025 y 2026.
2. Comparar nombres, orden, tipos y cantidad de columnas entre periodos.
3. Contrastar las columnas reales con el diccionario oficial.
4. Identificar el último mes con información disponible en 2026.
5. Determinar el grano real del dataset.
6. Definir las primeras reglas de calidad.
7. Diseñar la capa de transformación y el modelo analítico inicial.
8. Preparar la carga hacia PostgreSQL.

## Cautelas analíticas

El proyecto tendrá un enfoque descriptivo y diagnóstico.

Por tanto:

- un bajo nivel de devengado no demuestra ineficiencia;
- un pico de gasto no implica una irregularidad;
- una alerta analítica representa un patrón que requiere contexto adicional;
- una correlación no deberá presentarse como causalidad;
- las conclusiones deberán mantenerse dentro de las variables y granularidad disponibles en la fuente oficial.

## Autor

Proyecto personal de portafolio desarrollado como evidencia de competencias en:

- Data Analytics;
- Python;
- SQL;
- Business Intelligence;
- modelado de datos;
- automatización;
- calidad de datos;
- documentación técnica;
- Git y GitHub.