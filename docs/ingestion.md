# Ingesta de fuentes oficiales del MEF

## 1. Propósito

Este documento explica cómo preparar el entorno, descargar las fuentes oficiales utilizadas por Peru Public Budget Monitor y verificar la integridad de los archivos obtenidos.

La configuración de las fuentes se encuentra centralizada en:

```text
config/sources.yaml
```

Los archivos originales se almacenan localmente en:

```text
data/raw/
```

Los manifiestos de cada ejecución se generan en:

```text
data/manifests/
```

Los datasets y manifiestos generados no se versionan en GitHub.

---

## 2. Requisitos

- Python 3.12.
- Git.
- Conexión a internet.
- Espacio local suficiente.

La descarga completa del MVP requiere aproximadamente 7.2 GB de espacio, sin considerar las etapas posteriores de procesamiento.

---

## 3. Preparación del entorno

Desde la raíz del repositorio, crear el entorno virtual con Python 3.12:

```bash
py -3.12 -m venv .venv
```

Activar el entorno desde Git Bash:

```bash
source .venv/Scripts/activate
```

Instalar las dependencias:

```bash
python -m pip install -r requirements.txt
```

Comprobar la versión activa:

```bash
python --version
```

La salida esperada debe corresponder a Python 3.12.

---

## 4. Fuentes configuradas

El MVP incluye las siguientes fuentes:

- `mef_devengado_2024`
- `mef_devengado_2025`
- `mef_devengado_2026`
- `mef_devengado_dictionary`

Las URLs, Resource IDs, nombres de archivo, codificación y condición de mutabilidad se encuentran en:

```text
config/sources.yaml
```

---

## 5. Descargar una fuente

Por defecto, el proceso selecciona el diccionario oficial:

```bash
python -m src.extract
```

También puede indicarse una fuente explícitamente:

```bash
python -m src.extract \
  --source-id mef_devengado_dictionary
```

Ejemplo para descargar el recurso 2026:

```bash
python -m src.extract \
  --source-id mef_devengado_2026
```

---

## 6. Descargar todas las fuentes

Para descargar los cuatro recursos configurados:

```bash
python -m src.extract --all
```

El proceso realiza las siguientes actividades:

1. Lee la configuración YAML.
2. Descarga cada archivo por bloques.
3. Utiliza un archivo temporal con extensión `.part`.
4. Valida el tamaño y el contenido básico.
5. Calcula el hash SHA-256.
6. Reemplaza el archivo de destino únicamente después de validar la descarga.
7. Genera un manifiesto JSON por cada fuente procesada.

---

## 7. Forzar una descarga

La opción `--force` obliga a descargar nuevamente un recurso, aunque ya exista localmente.

Ejemplo:

```bash
python -m src.extract \
  --source-id mef_devengado_dictionary \
  --force
```

---

## 8. Estados de ejecución

Los manifiestos pueden registrar los siguientes estados:

| Estado | Significado |
|---|---|
| `success` | El archivo no existía y fue descargado correctamente |
| `updated` | El archivo existía y la versión oficial cambió |
| `unchanged` | La fuente mutable fue revisada y su contenido no cambió |
| `refreshed` | La descarga fue forzada, aunque el contenido era idéntico |
| `skipped_existing` | Se conservó una fuente inmutable ya existente |
| `failed` | La descarga no pudo completarse |

Las fuentes marcadas como mutables se descargan nuevamente para comparar su hash con la copia local.

---

## 9. Verificar la integridad

### Verificación rápida

Comprueba la existencia y el tamaño de los archivos sin recalcular sus hashes:

```bash
python -m src.verify_sources --quick
```

### Verificación completa

Recalcula el SHA-256 y compara cada archivo con su manifiesto más reciente:

```bash
python -m src.verify_sources
```

La verificación completa puede tardar varios minutos debido al tamaño de los archivos.

### Verificar una sola fuente

```bash
python -m src.verify_sources \
  --source-id mef_devengado_dictionary
```

Una fuente válida debe mostrar:

```text
OK | tamaño=True | hash=True
```

---

## 10. Ejecutar las pruebas

Para ejecutar todas las pruebas automatizadas:

```bash
python -m pytest -v
```

Las pruebas actuales validan:

- cálculo de SHA-256;
- detección de archivos vacíos;
- detección de descargas incompletas;
- rechazo de respuestas HTML;
- selección de fuentes;
- configuración de reintentos HTTP;
- tratamiento de fuentes mutables;
- clasificación de estados de descarga;
- selección del manifiesto más reciente;
- detección de archivos ausentes;
- detección de diferencias de tamaño;
- detección de modificaciones mediante hash.

---

## 11. Trazabilidad

Cada manifiesto registra, según el resultado de la ejecución:

- identificador de la fuente;
- nombre del recurso;
- URL oficial y URL de descarga;
- Resource ID;
- fecha y hora UTC;
- ruta local;
- formato y codificación configurada;
- tipo de contenido recibido;
- tamaño esperado y tamaño descargado;
- hash SHA-256 anterior y actual;
- indicador de cambio de contenido;
- estado de ejecución;
- duración del proceso;
- condición de mutabilidad;
- información del error, si corresponde;
- versión del pipeline.

Los manifiestos generados se almacenan localmente en:

```text
data/manifests/
```

Estos archivos no se versionan en GitHub, pero pueden regenerarse mediante el proceso de ingesta.