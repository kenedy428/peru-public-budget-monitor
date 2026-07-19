# Source manifests

Esta carpeta almacenará los manifiestos generados por cada ejecución del proceso de ingesta.

Un manifiesto registrará, como mínimo:

- identificador de la fuente;
- nombre del recurso;
- URL de descarga;
- fecha y hora de descarga;
- tamaño del archivo;
- hash SHA-256;
- estado de la descarga;
- ruta local;
- versión del pipeline.

Los manifiestos generados durante las ejecuciones no se versionarán en GitHub. Solo este archivo de documentación permanecerá en el repositorio.