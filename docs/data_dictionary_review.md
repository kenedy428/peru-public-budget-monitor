# Revisión del diccionario de datos del MEF

## 1. Fuente revisada

| Campo | Valor |
|---|---|
| Archivo | `data\raw\Gasto_Devengado_Diccionario.csv` |
| Manifiesto | `data\manifests\20260719T031134571873Z_mef_devengado_dictionary.json` |
| Recurso | Gasto_Devengado_Diccionario.csv |
| URL de origen | https://datosabiertos.mef.gob.pe/dataset/presupuesto-y-ejecucion-de-gasto-devengado-mensual/resource/d2aca9ca-2820-425e-826b-ee3a7a81c113 |
| Fecha de descarga UTC | 2026-07-19T03:11:34.570877+00:00 |
| Codificación | `utf-8-sig` |
| SHA-256 del manifiesto | `04d5bc96a55612458100fc7addf30853795489d4aca101bdf42a5e485f2c5947` |
| SHA-256 calculado | `04d5bc96a55612458100fc7addf30853795489d4aca101bdf42a5e485f2c5947` |
| Hash coincidente | Sí |
| Fuente mutable | True |

## 2. Validación estructural

| Control | Resultado |
|---|---:|
| Registros del diccionario | 73 |
| Columnas en staging | 73 |
| Variables duplicadas | 0 |
| Coincidencia exacta con staging | Sí |

### Variables del diccionario ausentes en staging

Ninguna.

### Columnas staging no documentadas

Ninguna.

## 3. Alcance del diccionario

El diccionario proporciona el nombre técnico, el tipo general y la descripción oficial de cada variable.

No contiene campos específicos para declarar claves primarias, cardinalidades, dependencias jerárquicas o vigencia histórica. Estos aspectos deben validarse posteriormente sobre los datos.

## 4. Definiciones oficiales

| N.º | Variable | Tipo de dato | Descripción |
|---:|---|---|---|
| 1 | `ANO_EJE` | Numérico | Año de ejecución del presupuesto. |
| 2 | `NIVEL_GOBIERNO` | Carácter | Código (letra) que identifica el Nivel de Gobierno: E, R, M; para Nacional, Regionales y Locales, respectivamente. |
| 3 | `NIVEL_GOBIERNO_NOMBRE` | Carácter | Descripción de Nivel de Gobierno: Nacional, Regionales, Locales. |
| 4 | `SECTOR` | Carácter | Código de Sector al que pertenece la Entidad. |
| 5 | `SECTOR_NOMBRE` | Carácter | Descripción de código del Sector al que pertenece la Entidad. |
| 6 | `PLIEGO` | Carácter | Código de Pliego al que pertenece la Entidad. |
| 7 | `PLIEGO_NOMBRE` | Carácter | Descripción de código del Pliego al que pertenece la Entidad. |
| 8 | `SEC_EJEC` | Carácter | Código que identifica a una Entidad. |
| 9 | `EJECUTORA` | Carácter | Código de la cadena institucional que identifica a una Entidad. |
| 10 | `EJECUTORA_NOMBRE` | Carácter | Nombre de la Entidad. |
| 11 | `DEPARTAMENTO_EJECUTORA` | Carácter | Código de departamento donde se ubica la Entidad. |
| 12 | `DEPARTAMENTO_EJECUTORA_NOMBRE` | Carácter | Nombre de departamento donde se ubica la Entidad. |
| 13 | `PROVINCIA_EJECUTORA` | Carácter | Código de provincia del departamento donde se ubica la Entidad. |
| 14 | `PROVINCIA_EJECUTORA_NOMBRE` | Carácter | Nombre de provincia del departamento donde se ubica la Entidad. |
| 15 | `DISTRITO_EJECUTORA` | Carácter | Código de distrito de la provincia del departamento donde se ubica la Entidad. |
| 16 | `DISTRITO_EJECUTORA_NOMBRE` | Carácter | Nombre de distrito de la provincia del departamento donde se ubica la Entidad. |
| 17 | `SEC_FUNC` | Numérico | Código de meta. |
| 18 | `PROGRAMA_PPTO` | Numérico | Código de Programa Presupuestal. |
| 19 | `PROGRAMA_PPTO_NOMBRE` | Carácter | Descripción del Programa Presupuestal. |
| 20 | `TIPO_ACT_PROY` | Numérico | Código que muestra si es proyecto o producto. |
| 21 | `PRODUCTO_PROYECTO` | Numérico | Código que identifica a un proyecto o producto. |
| 22 | `PRODUCTO_PROYECTO_NOMBRE` | Carácter | Descripción de un proyecto o producto. |
| 23 | `ACTIVIDAD_ACCION_OBRA` | Numérico | Código que identifica a una Actividad/Acción de inversioón u obra. |
| 24 | `ACTIVIDAD_ACCION_OBRA_NOMBRE` | Carácter | Descripción de una Actividad/Acción de inversión u obra. |
| 25 | `FUNCION` | Carácter | Código de Función. |
| 26 | `FUNCION_NOMBRE` | Carácter | Corresponde al nivel máximo de agregación de las acciones a tomar, orientadas a la ejecución de un determinado tema. |
| 27 | `DIVISION_FUNCIONAL` | Carácter | Código de División Funcional. |
| 28 | `DIVISION_FUNCIONAL_NOMBRE` | Carácter | Corresponde al nivel de agregación de las acciones a tomar, orientadas a la ejecución de un determinado tema. |
| 29 | `GRUPO_FUNCIONAL` | Carácter | Código de Grupo Funcional. |
| 30 | `GRUPO_FUNCIONAL_NOMBRE` | Carácter | Corresponde al tercer nivel de agregación de las acciones a tomar, orientadas a la ejecución de un determinado tema. |
| 31 | `META` | Carácter | Secuencial que se incrementará desde '00001' en adelante cada vez que exista para diferentes metas (sec_func) la misma combinación: Función + División Funcional + Grupo Funcional + Producto/Proyecto + Act/AccInv/Obra. Lo diferenciará la Finalidad. |
| 32 | `FINALIDAD` | Carácter | Código de Finalidad. |
| 33 | `META_NOMBRE` | Carácter | Descripción de la Finalidad. |
| 34 | `DEPARTAMENTO_META` | Carácter | Código de Departamento del Ubigeo de la meta. |
| 35 | `DEPARTAMENTO_META_NOMBRE` | Carácter | Nombre del departamento del Ubigeo de la meta. |
| 36 | `FUENTE_FINANCIAMIENTO` | Carácter | Código de la Fuente de Financimiento que agrupa a uno o más Rubros. |
| 37 | `FUENTE_FINANCIAMIENTO_NOMBRE` | Carácter | Descripción de la Fuente de Financiamiento. |
| 38 | `RUBRO` | Carácter | Código del Rubro que puede utilizar la Entidad. |
| 39 | `RUBRO_NOMBRE` | Carácter | Descripción del Rubro. |
| 40 | `TIPO_RECURSO` | Carácter | Código del Tipo de Recurso. |
| 41 | `TIPO_RECURSO_NOMBRE` | Carácter | Descripción del Tipo de Recurso. |
| 42 | `CATEGORIA_GASTO` | Numérico | Código de la Categoria de Gasto. |
| 43 | `CATEGORIA_GASTO_NOMBRE` | Carácter | Descripción de la Categoría de Gasto. |
| 44 | `TIPO_TRANSACCION` | Numérico | Número que identifica si es Gasto (2) o Ingreso (1). Para este reporte, siempre se presentará el número 2. |
| 45 | `TIPO_TRANSACCION_NOMBRE` | Carácter | Descripción del Tipo de transacción: Gastos Presupuestarios. |
| 46 | `GENERICA` | Numérico | Mayor nivel de agregación de los clasificadores de gasto. |
| 47 | `GENERICA_NOMBRE` | Carácter | Descripción de la Genérica. |
| 48 | `SUBGENERICA` | Numérico | Es el nivel intermedio de agregación (subgenérica nivel 1) de los clasificadores de gasto. |
| 49 | `SUBGENERICA_NOMBRE` | Carácter | Descripción de la subgenérica. |
| 50 | `SUBGENERICA_DET` | Numérico | Es el nivel intermedio de agregación (subgenérica nivel 2) de los clasificadores de gasto. |
| 51 | `SUBGENERICA_DET_NOMBRE` | Carácter | Descripción de la subgenérica detalle. |
| 52 | `ESPECIFICA` | Numérico | Código de Específica nivel 1. Identifica el detalle del gasto. |
| 53 | `ESPECIFICA_NOMBRE` | Carácter | Descripción de la específica. |
| 54 | `ESPECIFICA_DET` | Numérico | Código de Específica nivel 2. Identifica el detalle del gasto. |
| 55 | `ESPECIFICA_DET_NOMBRE` | Carácter | Descripción de la específica detalle. |
| 56 | `MONTO_PIA` | Numérico | Monto asignado de Presupuesto Institucional de Apertura. |
| 57 | `MONTO_PIM` | Numérico | Monto de Presupuesto Institucional Modificado. |
| 58 | `MONTO_CERTIFICADO_ANUAL` | Numérico | Monto del presupuesto utilizado en fase Certificación en el AÑO_EJE. |
| 59 | `MONTO_COMPROMETIDO_ANUAL` | Numérico | Monto del presupuesto utilizado en fase Compromiso anual en el AÑO_EJE. |
| 60 | `MONTO_DEVENGADO_ENERO` | Numérico | Monto ejecutado como fase Devengado en el mes de enero. |
| 61 | `MONTO_DEVENGADO_FEBRERO` | Numérico | Monto ejecutado como fase Devengado en el mes de febrero. |
| 62 | `MONTO_DEVENGADO_MARZO` | Numérico | Monto ejecutado como fase Devengado en el mes de marzo. |
| 63 | `MONTO_DEVENGADO_ABRIL` | Numérico | Monto ejecutado como fase Devengado en el mes de abril. |
| 64 | `MONTO_DEVENGADO_MAYO` | Numérico | Monto ejecutado como fase Devengado en el mes de mayo. |
| 65 | `MONTO_DEVENGADO_JUNIO` | Numérico | Monto ejecutado como fase Devengado en el mes de junio. |
| 66 | `MONTO_DEVENGADO_JULIO` | Numérico | Monto ejecutado como fase Devengado en el mes de julio. |
| 67 | `MONTO_DEVENGADO_AGOSTO` | Numérico | Monto ejecutado como fase Devengado en el mes de agosto. |
| 68 | `MONTO_DEVENGADO_SEPTIEMBRE` | Numérico | Monto ejecutado como fase Devengado en el mes de septiembre. |
| 69 | `MONTO_DEVENGADO_OCTUBRE` | Numérico | Monto ejecutado como fase Devengado en el mes de octubre. |
| 70 | `MONTO_DEVENGADO_NOVIEMBRE` | Numérico | Monto ejecutado como fase Devengado en el mes de noviembre. |
| 71 | `MONTO_DEVENGADO_DICIEMBRE` | Numérico | Monto ejecutado como fase Devengado en el mes de diciembre. |
| 72 | `MONTO_DEVENGADO_ANUAL` | Numérico | Monto ejecutado como fase Devengado en el AÑO_EJE. |
| 73 | `MONTO_GIRADO_ANUAL` | Numérico | Monto ejecutado como fase Girado en el AÑO_EJE. |

## 5. Conclusión de esta revisión

Las definiciones del diccionario se utilizarán para interpretar las variables y formular hipótesis de modelado.

Las claves naturales, relaciones y jerarquías solo se aceptarán después de validarlas con los datos reales almacenados en PostgreSQL.
