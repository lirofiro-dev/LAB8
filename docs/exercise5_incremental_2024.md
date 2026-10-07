# Ejercicio 5 - Incorporacion de datos 2024

Este ejercicio amplio el sistema de descarga para incorporar datos de taxis amarillos y verdes correspondientes a 2024, conservando los archivos 2026 previamente descargados.

Archivo SQL asociado: `sql/exercise5_incremental_2024_validation.sql`.

## Cambios realizados al sistema de descarga

El script `scripts/download_data.py` fue modificado para aceptar multiples anios con el argumento `--years`.

Ejemplos de uso:

```bash
python scripts/download_data.py
python scripts/download_data.py --years 2026
python scripts/download_data.py --years 2024 2026
python scripts/download_data.py --taxi yellow --years 2024
```

El valor por defecto final del laboratorio descarga `2024`, `2025` y `2026` para taxis `yellow` y `green`. Para reproducir solamente este ejercicio puede usarse `--years 2024 2026`. El script conserva el comportamiento incremental: si un archivo ya existe localmente y tiene tamano mayor a cero, no se descarga de nuevo.

## Resultado de la descarga incremental

Comando ejecutado dentro del contenedor:

```bash
docker compose exec lab python scripts/download_data.py
```

Resultado:

- 24 archivos nuevos descargados para 2024.
- 16 archivos de 2026 omitidos porque ya existian.
- 8 archivos de 2026 no publicados por la TLC al momento de la ejecucion.
- 0 archivos fallidos.

Se ejecuto el script una segunda vez para validar el comportamiento incremental. Resultado:

- 0 archivos descargados.
- 40 archivos omitidos porque ya existian.
- 8 archivos de 2026 no publicados por la TLC.
- 0 archivos fallidos.

Archivos locales despues de la descarga:

| taxi_type | anio | archivos |
|---|---:|---:|
| green | 2024 | 12 |
| green | 2026 | 8 |
| yellow | 2024 | 12 |
| yellow | 2026 | 8 |

Total: 40 archivos Parquet locales.

## Validacion con DuckDB

La validacion se realizo directamente sobre los archivos Parquet usando `read_parquet` y el parametro `filename = true` para extraer el anio desde la ruta del archivo.

Resultado de archivos y filas por anio de archivo:

| taxi_type | file_year | files | rows |
|---|---:|---:|---:|
| green | 2024 | 12 | 660218 |
| green | 2026 | 8 | 337114 |
| yellow | 2024 | 12 | 41169720 |
| yellow | 2026 | 8 | 29703355 |

Resultado de consulta conjunta usando anio del archivo y anio del pickup:

| taxi_type | file_year | pickup_year | rows | avg_total_amount |
|---|---:|---:|---:|---:|
| green | 2024 | 2024 | 660198 | 24.26 |
| green | 2026 | 2026 | 337100 | 25.49 |
| yellow | 2024 | 2024 | 41169664 | 27.83 |
| yellow | 2024 | 2026 | 2 | 43.29 |
| yellow | 2026 | 2026 | 29703338 | 30.07 |

## Decisiones tomadas

- Para validar disponibilidad de archivos se usa el anio extraido de la ruta (`file_year`), no solo el anio de `pickup_datetime`, porque existen registros con fechas fuera del anio del archivo.
- Las consultas del Ejercicio 4 pueden ampliarse a multiples anios cambiando el patron de lectura a `data/raw/<tipo>/**/*.parquet` y agregando `file_year` o `YEAR(pickup_datetime)` segun la pregunta.
- Para analisis temporal estricto se recomienda filtrar `YEAR(pickup_datetime) = file_year` o documentar explicitamente si se incluyen registros fuera del anio del archivo.

## Caracteristicas del diseno que permiten incorporar nuevos datos

- Los archivos se organizan por `data/raw/<tipo>/<anio>/`, lo que permite agregar anios sin mezclar fuentes.
- El script construye nombres y rutas a partir de `tipo`, `anio` y `mes`.
- El uso de patrones glob (`**/*.parquet`) permite consultar nuevos archivos sin listar cada archivo manualmente.
- El script verifica existencia local antes de descargar, por lo que puede ejecutarse repetidamente sin duplicar trabajo.
