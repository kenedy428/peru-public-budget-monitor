# Datos procesados

Esta carpeta contiene los archivos generados por la etapa de transformación y consolidación de las fuentes oficiales del MEF.

Los archivos procesados se generan reproduciblemente a partir de la capa `data/raw/` y no se almacenan en Git debido a su tamaño.

La transformación deberá:

- preservar intactos los archivos originales;
- normalizar códigos, textos y medidas monetarias;
- consolidar registros mediante `business_key_v1`;
- sumar las 18 columnas monetarias;
- conservar los atributos no monetarios asociados al grano;
- verificar la conservación de los totales;
- generar reportes de reconciliación.

Los archivos procesados serán utilizados posteriormente para la carga en PostgreSQL.