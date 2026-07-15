# Alcance del proyecto

## 1. Descripción general

El proyecto Peru Public Budget Monitor es una solución analítica end-to-end orientada a transformar datos oficiales de ejecución presupuestal pública del Ministerio de Economía y Finanzas del Perú (MEF) en información reproducible, trazable y útil para el análisis.

El proyecto abarcará el ciclo completo de los datos: extracción o ingesta de la fuente, perfilado, validación de calidad, transformación, almacenamiento relacional, modelado analítico, análisis exploratorio, definición de KPIs, visualización mediante dashboard, validación cruzada, automatización y documentación técnica.

---

## 2. Planteamiento del problema

La información sobre gasto público en el Perú se encuentra disponible mediante fuentes oficiales de datos abiertos. Sin embargo, convertir archivos extensos y potencialmente heterogéneos en información confiable, comparable y reproducible requiere múltiples pasos técnicos y analíticos.

Los usuarios interesados en monitorear la ejecución presupuestal necesitan una forma eficiente de:

- Comparar la evolución del gasto devengado a lo largo del tiempo.
- Analizar diferencias entre niveles de gobierno, entidades, territorios y clasificaciones presupuestales.
- Identificar patrones atípicos o cambios abruptos que requieran un análisis contextual adicional.
- Acceder a resultados reproducibles sin reconstruir manualmente todo el proceso de preparación de datos en cada nuevo periodo.

Este proyecto busca reducir esa fricción mediante la construcción de un pipeline de datos reproducible y una capa analítica estructurada.

---

## 3. Usuarios objetivo

### Analistas de presupuesto y planeamiento

Necesitan monitorear la evolución del gasto y comparar entidades o grupos con características similares.

### Equipos de control interno y auditoría

Necesitan información analítica trazable que permita priorizar áreas que podrían requerir una revisión adicional, sin considerar las señales analíticas como evidencia de irregularidad.

### Periodistas de datos e investigadores

Necesitan datos limpios y estructurados que permitan realizar análisis temporales, territoriales, institucionales y presupuestales.

### Ciudadanos interesados

Necesitan una vista accesible que permita entender cómo evoluciona el gasto público y dónde se concentra.



## 4. Preguntas iniciales de negocio

La primera versión del proyecto buscará responder las siguientes preguntas:

1. ¿Cómo evoluciona el monto devengado mensual y acumulado a lo largo del tiempo?
2. ¿Qué diferencias existen entre el Gobierno Nacional, los Gobiernos Regionales y los Gobiernos Locales?
3. ¿Qué entidades presentan valores consistentemente por encima o por debajo de grupos comparables?
4. ¿En qué meses se concentran los mayores picos de devengado?
5. ¿Qué clasificaciones presupuestales o funciones concentran los mayores montos de gasto?
6. ¿Qué entidades presentan cambios interanuales abruptos o patrones analíticamente atípicos?
7. ¿Qué tan estables son los rankings de entidades o regiones a lo largo del tiempo?
8. ¿Qué hallazgos se mantienen al filtrar por nivel de gobierno, territorio, entidad o clasificación presupuestal?

Estas preguntas podrán ser ajustadas después de revisar el diccionario oficial de datos y la estructura real de los archivos descargados.

---

## 5. Alcance del MVP

El Minimum Viable Product incluirá inicialmente:

- Datos oficiales de devengado mensual del MEF correspondientes a 2024 y 2025.
- Proceso reproducible de extracción o ingesta.
- Registro de metadatos de la fuente y hash SHA-256.
- Perfilado de datos y comparación de esquemas.
- Reglas de calidad y reportes por ejecución.
- Transformación de datos mediante Python y pandas.
- Almacenamiento relacional en PostgreSQL.
- Modelo dimensional analítico.
- Consultas SQL analíticas avanzadas.
- Análisis Exploratorio de Datos (EDA).
- Al menos cinco KPIs definidos.
- Dashboard en Power BI.
- Validación y reconciliación mediante Excel.
- Pruebas unitarias y validaciones SQL.
- Documentación profesional en GitHub.

---

## 6. Fuera del alcance del MVP

Los siguientes elementos quedan deliberadamente fuera del alcance inicial:

- Machine learning sin una pregunta analítica que lo justifique.
- Predicción del gasto público.
- Web scraping frágil cuando existen fuentes oficiales descargables.
- Múltiples dashboards duplicados en diferentes herramientas de BI.
- Una aplicación web completa.
- Afirmaciones causales sobre el comportamiento del gasto.
- Clasificación de comportamientos atípicos como corrupción, ineficiencia o irregularidad.

Estos elementos solo podrán reconsiderarse cuando el pipeline principal esté completo, probado, reconciliado y documentado.

---

## 7. Criterios de éxito

El MVP será considerado satisfactorio cuando:

- La fuente oficial y su diccionario de datos estén correctamente documentados.
- Los datos de 2024 y 2025 puedan procesarse sin ajustes manuales ocultos.
- El pipeline registre metadatos de la fuente y resultados de calidad.
- Los errores críticos de calidad detengan la carga correspondiente.
- Los principales totales y conteos sean reconciliados contra las fuentes originales.
- El modelo analítico tenga un grano claramente definido.
- El análisis SQL incluya JOINs, CTEs, subconsultas, agregaciones y funciones de ventana.
- El dashboard responda preguntas de negocio previamente definidas.
- No se almacenen credenciales ni información sensible en GitHub.
- Una nueva persona pueda comprender y reproducir el proyecto siguiendo la documentación.

---

## 8. Cautelas analíticas

Este proyecto tendrá un enfoque descriptivo y diagnóstico.

Por tanto:

- Un nivel bajo de devengado no demuestra ineficiencia.
- Un pico de gasto no implica una irregularidad.
- Las alertas analíticas representan patrones que requieren contexto adicional, no acusaciones.
- Los cambios en nombres institucionales o códigos de clasificación entre años deberán documentarse.
- Una correlación no deberá presentarse como causalidad.
- Todas las conclusiones deberán mantenerse dentro de las variables y la granularidad realmente disponibles en la fuente oficial.