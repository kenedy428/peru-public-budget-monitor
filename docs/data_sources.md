# Fuentes de datos

## 1. Propósito del documento

Este documento registra las fuentes oficiales utilizadas en el proyecto Peru Public Budget Monitor, incluyendo su procedencia, cobertura temporal, recursos disponibles, mecanismos de acceso y decisiones de alcance.

Su finalidad es garantizar la trazabilidad y reproducibilidad del pipeline, permitiendo identificar con claridad de dónde provienen los datos utilizados en cada ejecución.

---

## 2. Fuente principal

### Nombre del dataset

**Presupuesto y Ejecución de Gasto – Devengado Mensual**

### Entidad responsable

Ministerio de Economía y Finanzas del Perú (MEF).

### Portal

Portal de Datos Abiertos del Ministerio de Economía y Finanzas.

### Descripción

El dataset contiene información del gasto público en formato de devengado mensual correspondiente a:

- Gobierno Nacional.
- Gobiernos Regionales.
- Gobiernos Locales.

La cobertura temporal disponible actualmente comprende información desde 2012 hasta 2026.

### Fecha de consulta inicial

14 de julio de 2026.

---

## 3. Recursos seleccionados para el MVP

El MVP utilizará inicialmente los siguientes recursos:

| Año | Recurso | Uso en el proyecto |
|---|---|---|
| 2024 | `2024-Gasto-Devengado.csv` | Primer año completo de referencia |
| 2025 | `2025-Gasto-Devengado-Mensual.csv` | Segundo año completo de referencia |
| 2026 | `2026-Gasto-Devengado-Mensual.csv` | Año en curso para análisis actualizado y comparaciones YTD |
| N/A | `Gasto_Devengado_Diccionario.csv` | Definición oficial de campos y variables |

Las URLs específicas, Resource IDs y demás metadatos técnicos de los recursos seleccionados fueron verificados individualmente en el Portal de Datos Abiertos del MEF. Los metadatos físicos de cada descarga, como tamaño, hash y timestamp, se registrarán durante la ejecución del pipeline.

---
## 4. Registro técnico de recursos

### Recurso 2024

| Campo | Valor |
|---|---|
| Dataset | Presupuesto y Ejecución de Gasto – Devengado Mensual |
| Año de referencia | 2024 |
| Nombre del recurso | `2024-Gasto-Devengado.csv` |
| Tipo de periodo | Año completo |
| Formato | CSV |
| Fuente | Ministerio de Economía y Finanzas del Perú |
| Mecanismo de acceso | Descarga directa y API de datos |
| URL de la página del recurso | `https://datosabiertos.mef.gob.pe/dataset/presupuesto-y-ejecucion-de-gasto-devengado-mensual/resource/0d38c6bd-8f1b-474d-ade3-32c97260f78a` |
| URL de descarga directa | `https://fs.datosabiertos.mef.gob.pe/datastorefiles/2024-Gasto-Devengado.csv` |
| Resource ID | `0d38c6bd-8f1b-474d-ade3-32c97260f78a` |
| Registros mostrados por el portal | 2,789,753 |
| Fecha de consulta | 15 de julio de 2026 |
| Estado | Página y mecanismos de acceso verificados; pendiente descarga e inspección técnica del archivo |

### Recurso 2025

| Campo | Valor |
|---|---|
| Dataset | Presupuesto y Ejecución de Gasto – Devengado Mensual |
| Año de referencia | 2025 |
| Nombre del recurso | `2025-Gasto-Devengado-Mensual.csv` |
| Tipo de periodo | Año cerrado; cobertura mensual pendiente de validar en el archivo |
| Formato | CSV |
| Fuente | Ministerio de Economía y Finanzas del Perú |
| Mecanismo de acceso | Descarga directa y API de datos |
| URL de la página del recurso | `https://datosabiertos.mef.gob.pe/dataset/presupuesto-y-ejecucion-de-gasto-devengado-mensual/resource/8a5a9a6f-1702-4329-8730-67f46e2de2a8` |
| URL de descarga directa | `https://fs.datosabiertos.mef.gob.pe/datastorefiles/2025-Gasto-Devengado-Mensual.csv` |
| Resource ID | `8a5a9a6f-1702-4329-8730-67f46e2de2a8` |
| Registros mostrados por el portal | 2,807,163 |
| Fecha de consulta | 15 de julio de 2026 |
| Estado | Página y mecanismos de acceso verificados; pendiente descarga e inspección técnica del archivo |

### Recurso 2026

| Campo | Valor |
|---|---|
| Dataset | Presupuesto y Ejecución de Gasto – Devengado Mensual |
| Año de referencia | 2026 |
| Nombre del recurso | `2026-Gasto-Devengado-Mensual.csv` |
| Tipo de periodo | Año en curso; último mes disponible pendiente de validar |
| Formato | CSV |
| Fuente | Ministerio de Economía y Finanzas del Perú |
| Mecanismo de acceso | Descarga directa y API de datos |
| URL de la página del recurso | `https://datosabiertos.mef.gob.pe/dataset/presupuesto-y-ejecucion-de-gasto-devengado-mensual/resource/c698c1cd-30f5-4a63-8a77-39484bab1f58` |
| URL de descarga directa | `https://fs.datosabiertos.mef.gob.pe/datastorefiles/2026-Gasto-Devengado-Mensual.csv` |
| Resource ID | `c698c1cd-30f5-4a63-8a77-39484bab1f58` |
| Registros mostrados por el portal | 2,101,712 |
| Fecha de consulta | 15 de julio de 2026 |
| Estado | Página y mecanismos de acceso verificados; pendiente descarga e inspección técnica del archivo |

### Diccionario oficial de datos

| Campo | Valor |
|---|---|
| Dataset | Presupuesto y Ejecución de Gasto – Devengado Mensual |
| Nombre del recurso | `Gasto_Devengado_Diccionario.csv` |
| Tipo de recurso | Diccionario de datos |
| Formato | CSV |
| Fuente | Ministerio de Economía y Finanzas del Perú |
| Mecanismo de acceso | Descarga directa y API de datos |
| URL de la página del recurso | `https://datosabiertos.mef.gob.pe/dataset/presupuesto-y-ejecucion-de-gasto-devengado-mensual/resource/d2aca9ca-2820-425e-826b-ee3a7a81c113` |
| URL de descarga directa | `https://fs.datosabiertos.mef.gob.pe/datastorefiles/Gasto_Devengado_Diccionario.csv` |
| Resource ID | `d2aca9ca-2820-425e-826b-ee3a7a81c113` |
| Registros mostrados por el portal | 73 |
| Tamaño informado | 6.68 KB |
| Fecha de creación | 26 de abril de 2023 |
| Última actualización informada | 10 de octubre de 2025, 17:39 |
| MIME type | `text/csv` |
| Estado del recurso | Activo |
| Fecha de consulta | 15 de julio de 2026 |
| Estado de investigación | Página y mecanismos de acceso verificados; pendiente descarga y revisión completa del contenido |

---

## 5. Decisión de alcance temporal

Aunque la fuente oficial dispone de una serie histórica más amplia, el MVP utilizará inicialmente los años completos 2024 y 2025, además de 2026 hasta el último periodo mensual disponible.

Esta decisión busca:

- trabajar con dos años completos y consecutivos como base histórica;
- incorporar información actualizada del año 2026;
- permitir comparaciones interanuales mediante periodos equivalentes YTD;
- verificar diferencias de esquema antes de ampliar la serie histórica;
- priorizar calidad, trazabilidad y reproducibilidad;
- diseñar el pipeline para admitir nuevos cortes mensuales de 2026 sin rehacer manualmente el proceso.

Las comparaciones entre 2026 y años anteriores deberán realizarse utilizando el mismo número de meses disponibles. No se comparará directamente un año incompleto contra un año completo.

La ampliación hacia la serie histórica completa se considerará después de completar y validar satisfactoriamente el MVP.

---

## 6. Mecanismos de acceso identificados

La fuente oficial presenta potencialmente los siguientes mecanismos de acceso:

1. Descarga directa de archivos CSV.
2. API de datos del portal basada en CKAN.

### Prueba técnica de acceso

El 16 de julio de 2026 se realizó una prueba controlada utilizando el recurso `Gasto_Devengado_Diccionario.csv`.

#### Descarga directa

La descarga directa permitió obtener el archivo CSV completo mediante una sola solicitud.

Resultados obtenidos:

- Tamaño descargado: 6,841 bytes.
- Registros de datos: 73.
- Filas físicas: 74, incluyendo la cabecera.
- Tipo detectado: `text/csv`.
- Codificación detectada: UTF-8.
- El archivo contiene una marca BOM al inicio del primer encabezado.
- Para su lectura correcta en Python se deberá utilizar `encoding="utf-8-sig"` o eliminar explícitamente el BOM.
- Hash SHA-256:

`04d5bc96a55612458100fc7addf9368537954804dca101bdf42a5e485f2c5947`

En el entorno Windows utilizado para la prueba, `curl` necesitó la opción `--ssl-revoke-best-effort` debido a una limitación de Schannel al comprobar la revocación del certificado.

#### API oficial

La API oficial fue probada mediante el endpoint:

`https://api.datosabiertos.mef.gob.pe/DatosAbiertos/v1/datastore_search`

La consulta utilizó el Resource ID:

`d2aca9ca-2820-425e-826b-ee3a7a81c113`

Resultados obtenidos:

- Tipo de respuesta: `application/json`.
- Codificación: UTF-8.
- Registros recuperados: 73.
- Las variables obtenidas mediante la API coinciden con las del CSV.
- El contenido completo de los 73 registros resultó equivalente entre ambos mecanismos.
- La respuesta incluye información de navegación mediante el campo `next`.
- El archivo JSON resultó mayor que el CSV debido a que repite los nombres de los campos y agrega metadatos de consulta.

### Estrategia seleccionada

Para el MVP se utilizará:

- **Descarga directa de CSV como mecanismo principal de ingesta**, especialmente para los archivos anuales que contienen millones de registros.
- **API como mecanismo complementario**, destinado a consultas pequeñas, validaciones, muestreos y comprobaciones específicas.

Esta decisión se basa en que la descarga directa permite recuperar el archivo completo con menor sobrecarga, mientras que la API facilita consultas filtradas, pero requiere manejar paginación y genera respuestas de mayor tamaño relativo.
---

## 7. Diccionario de datos

La fuente oficial dispone de un recurso específico denominado:

`Gasto_Devengado_Diccionario.csv`

Este diccionario será utilizado para:

- comprender el significado de las columnas;
- validar tipos de datos;
- distinguir códigos de descripciones;
- definir columnas críticas;
- establecer reglas de calidad;
- determinar el grano real de los datos;
- ajustar las preguntas de negocio y KPIs.

No se definirá el modelo dimensional definitivo hasta revisar el diccionario y las columnas reales de los archivos 2024, 2025 y 2026.

---

## 8. Metadatos que deberán registrarse por archivo

Cada archivo fuente utilizado en el pipeline deberá tener asociados, como mínimo, los siguientes metadatos:

| Campo | Descripción |
|---|---|
| `source_name` | Nombre de la fuente |
| `resource_name` | Nombre del archivo o recurso |
| `source_url` | URL oficial |
| `download_url` | URL de descarga directa, si corresponde |
| `access_date` | Fecha de acceso |
| `download_timestamp` | Fecha y hora efectiva de descarga |
| `reference_year` | Año al que corresponde el archivo |
| `file_format` | Formato del archivo |
| `file_size_bytes` | Tamaño del archivo |
| `sha256_hash` | Hash SHA-256 del archivo descargado |
| `pipeline_version` | Versión del pipeline que procesó la fuente |

---
## 9. Hallazgos confirmados durante la investigación

### Recurso 2024

La inspección de la página oficial del recurso `2024-Gasto-Devengado.csv` permitió confirmar lo siguiente:

- El recurso corresponde al año fiscal 2024.
- El archivo se encuentra disponible en formato CSV.
- El portal permite tanto la descarga directa como el acceso mediante una API de datos.
- Al momento de la consulta, el explorador del portal mostraba 2,789,753 registros.
- La descripción oficial indica que el dataset contiene información del Presupuesto Institucional de Apertura (PIA), Presupuesto Institucional Modificado (PIM) y ejecución del gasto en las fases de Compromiso, Devengado y Girado.
- La información del Devengado se presenta mediante campos separados para cada mes.
- Las variables de Compromiso y Girado presentan valores anuales.
- La información corresponde a Unidades Ejecutoras del Gobierno Nacional, Gobiernos Regionales y municipalidades de los Gobiernos Locales.

Estos hallazgos deberán ser contrastados posteriormente contra el diccionario oficial y la estructura real del archivo descargado antes de definir KPIs, tipos de datos o el modelo dimensional definitivo.


### Recurso 2025

La inspección de la página oficial del recurso `2025-Gasto-Devengado-Mensual.csv` permitió confirmar lo siguiente:

- El recurso corresponde al año fiscal 2025.
- El archivo se encuentra disponible en formato CSV.
- El portal permite la descarga directa y el acceso mediante una API de datos.
- Al momento de la consulta, el explorador del portal mostraba 2,807,163 registros.
- La descripción oficial indica que contiene información del Presupuesto Institucional de Apertura (PIA), Presupuesto Institucional Modificado (PIM) y ejecución del gasto en las fases de Compromiso, Devengado y Girado.
- La información del Devengado se presenta mediante campos separados para cada mes.
- Las variables de Compromiso y Girado presentan valores anuales.
- La información corresponde a Unidades Ejecutoras del Gobierno Nacional, Gobiernos Regionales y municipalidades de los Gobiernos Locales.
- Los primeros campos visibles en el explorador presentan una nomenclatura similar a la observada en 2024, pero la equivalencia completa del esquema todavía debe comprobarse mediante el diccionario y los archivos descargados.

La cobertura de los meses, los tipos de datos, la codificación, los valores nulos y la compatibilidad estructural con 2024 deberán validarse mediante la inspección técnica del archivo.

### Recurso 2026

La inspección de la página oficial del recurso `2026-Gasto-Devengado-Mensual.csv` permitió confirmar lo siguiente:

- El recurso corresponde al año fiscal 2026.
- El archivo se encuentra disponible en formato CSV.
- El recurso corresponde a información con actualización mensual.
- El portal permite la descarga directa y el acceso mediante una API de datos.
- Al momento de la consulta, el explorador del portal mostraba 2,101,712 registros.
- La descripción oficial indica que contiene información del Presupuesto Institucional de Apertura (PIA), Presupuesto Institucional Modificado (PIM) y ejecución del gasto en las fases de Compromiso, Devengado y Girado.
- La información del Devengado se presenta mediante campos separados para cada mes.
- Las variables de Compromiso y Girado presentan valores anuales.
- Los primeros campos visibles presentan una nomenclatura similar a la observada en los recursos 2024 y 2025.
- La cantidad de registros es menor que la observada en 2024 y 2025, pero esta diferencia no debe interpretarse sin revisar el periodo efectivamente disponible y la estructura real del archivo.

La descarga e inspección técnica deberán determinar el último mes con información, la población de las columnas mensuales y la compatibilidad estructural con los recursos 2024 y 2025.

### Diccionario oficial de datos

La inspección de la página oficial de `Gasto_Devengado_Diccionario.csv` permitió confirmar lo siguiente:

- El recurso se encuentra disponible en formato CSV.
- El portal permite la descarga directa y el acceso mediante una API de datos.
- El diccionario contiene 73 registros.
- Su estructura está compuesta por los campos `TIPO_DATO`, `DESCRIPCION` y `VARIABLE`.
- Cada registro describe una variable de los archivos de ejecución presupuestal e indica su tipo de dato y significado.
- Entre las variables visibles se encuentran `ANO_EJE`, `NIVEL_GOBIERNO`, `SECTOR`, `SECTOR_NOMBRE`, `PLIEGO` y `PLIEGO_NOMBRE`.
- La presencia de variables de código y nombre confirma que el dataset diferencia identificadores de sus respectivas descripciones en varios niveles de clasificación.
- El recurso registra como última actualización el 10 de octubre de 2025.

El contenido completo deberá descargarse y compararse con las columnas reales de los archivos 2024, 2025 y 2026 antes de definir tipos, claves, reglas de calidad o el modelo dimensional.

---


## 10. Preguntas pendientes de investigación

Antes de iniciar la extracción se deberá resolver lo siguiente:

- ¿Los archivos pueden descargarse mediante una URL directa estable?
- ¿La API permite recuperar el dataset completo de manera eficiente?
- ¿Los archivos utilizan la misma codificación?
- ¿Existe alguna diferencia en nombres, tipos o cantidad de columnas?
- ¿Qué representa exactamente una fila del dataset?
- ¿Cuáles son los nombres exactos, tipos y reglas de población de las columnas mensuales de Devengado?
- ¿Hasta qué mes se encuentra actualizado actualmente el recurso 2026?
- ¿El archivo 2026 conserva el mismo esquema que 2024 y 2025?
- ¿La URL o el archivo 2026 se actualiza sobre el mismo recurso o se publica uno nuevo?
- ¿Cómo identificaremos programáticamente el último mes disponible?
- ¿Cómo garantizaremos que las comparaciones YTD utilicen periodos equivalentes?
- ¿Todas las columnas presentes en 2026 están documentadas en el diccionario cuya última actualización corresponde a 2025?

Estas preguntas deberán responderse mediante evidencia obtenida directamente de la fuente, el diccionario y el perfilado inicial de los datos.

---

## 11. Estado de la investigación

**Estado actual:** Identificación documental completada.

Se verificaron las páginas oficiales, URLs de descarga, Resource IDs, formatos y mecanismos de acceso de los recursos correspondientes a 2024, 2025, 2026 y el diccionario oficial de datos.

Se encuentra pendiente descargar los archivos, registrar sus metadatos físicos, revisar la codificación, comparar sus esquemas, comprobar la cobertura mensual de 2026 y evaluar el mecanismo definitivo de extracción.

## 12. Observaciones y riesgos de trazabilidad

### Observación inicial sobre nomenclatura

Los recursos seleccionados no siguen exactamente la misma convención de nombres:

- `2024-Gasto-Devengado.csv`
- `2025-Gasto-Devengado-Mensual.csv`
- `2026-Gasto-Devengado-Mensual.csv`

Esta diferencia de nomenclatura no implica por sí sola una diferencia de esquema, pero deberá considerarse durante el diseño de la configuración de fuentes y la comparación estructural de los archivos.

### Observación sobre la vigencia del diccionario

El diccionario oficial registra una última actualización anterior a la publicación del recurso mensual 2026.

Por ello, durante el perfilado se deberá comprobar:

- si todas las columnas de 2026 aparecen documentadas;
- si existen columnas nuevas, eliminadas o renombradas;
- si los tipos descritos coinciden con los valores reales;
- si alguna variable del diccionario ya no se encuentra en los archivos;
- si el orden de las columnas cambió entre periodos.

La ausencia de una variable en el diccionario o la presencia de columnas no documentadas deberá registrarse como una observación de calidad y trazabilidad.