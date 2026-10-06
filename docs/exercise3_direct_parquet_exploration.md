# Ejercicio 3 - Consultas directas sobre Parquet

Este documento registra la exploracion inicial realizada con DuckDB sobre los archivos Parquet descargados en `data/raw/` para el anio 2026.

Archivo SQL asociado: `sql/exercise3_direct_parquet_exploration.sql`.

## Fuente de datos

- Taxis amarillos: `data/raw/yellow/2026/*.parquet`.
- Taxis verdes: `data/raw/green/2026/*.parquet`.
- Estrategia: consultas directas con `read_parquet`, sin importar previamente los datos a una tabla.

## Consultas y resultados

### Cantidad de archivos disponibles

Objetivo: verificar cuantos archivos Parquet existen por tipo de taxi.

Consulta: ver seccion `3.1 Cantidad de archivos disponibles por tipo de taxi` en el archivo SQL.

Resultado:

| taxi_type | files |
|---|---:|
| green | 8 |
| yellow | 8 |

Decision: el conjunto local contiene 16 archivos Parquet publicados por la TLC al momento de la descarga.

### Meses disponibles

Objetivo: confirmar que meses estan presentes en los nombres de archivo.

Consulta: ver seccion `3.1 Meses disponibles por tipo de taxi` en el archivo SQL.

Resultado: existen archivos para enero, febrero, marzo, abril, mayo, junio, julio y agosto de 2026 para ambos tipos de taxi.

Decision: septiembre a diciembre no se consideran faltantes locales porque el script de descarga confirmo que aun no estaban publicados por la TLC.

### Cantidad de registros disponibles

Objetivo: contar los viajes disponibles por tipo de taxi sin materializar tablas.

Consulta: ver seccion `3.2 Cantidad de registros disponibles` en el archivo SQL.

Resultado:

| taxi_type | rows |
|---|---:|
| green | 337114 |
| yellow | 29703355 |

Decision: el volumen de taxis amarillos es mucho mayor que el de taxis verdes, por lo que las consultas posteriores deben separar o etiquetar el tipo de taxi para evitar interpretaciones sesgadas.

### Columnas y tipos de datos

Objetivo: identificar la estructura de los archivos.

Consulta: ver secciones `3.3 y 3.4` en el archivo SQL.

Resultado resumido:

| tipo | columnas | observaciones |
|---|---:|---|
| yellow | 20 | Usa `tpep_pickup_datetime` y `tpep_dropoff_datetime`. Incluye `Airport_fee`. |
| green | 21 | Usa `lpep_pickup_datetime` y `lpep_dropoff_datetime`. Incluye `ehail_fee` y `trip_type`. |

Columnas comunes relevantes:

- `VendorID`
- `passenger_count`
- `trip_distance`
- `RatecodeID`
- `store_and_fwd_flag`
- `PULocationID`
- `DOLocationID`
- `payment_type`
- `fare_amount`
- `extra`
- `mta_tax`
- `tip_amount`
- `tolls_amount`
- `improvement_surcharge`
- `total_amount`
- `congestion_surcharge`
- `cbd_congestion_fee`

Decision: para consultas conjuntas sera necesario normalizar nombres de columnas de fecha, porque yellow y green usan prefijos diferentes (`tpep` y `lpep`).

### Muestra de registros

Objetivo: inspeccionar ejemplos de filas reales.

Consulta: ver secciones `3.5` en el archivo SQL.

Resultado observado:

| taxi_type | pickup_datetime | passenger_count | trip_distance | total_amount | payment_type |
|---|---|---:|---:|---:|---:|
| yellow | 2026-01-01 00:54:04 | 1 | 0.97 | 15.86 | 1 |
| yellow | 2026-01-01 00:34:04 | 0 | 0.90 | 13.65 | 2 |
| green | 2026-01-01 00:27:58 | 2 | 6.20 | 45.20 | 1 |
| green | 2026-01-01 00:44:33 | 5 | 5.36 | 61.20 | 1 |

Decision: desde la muestra ya se observan casos de `passenger_count = 0`, por lo que esta variable debe revisarse como posible problema de calidad.

### Problemas iniciales de calidad de datos

Objetivo: detectar valores nulos, inconsistentes o atipicos desde la exploracion inicial.

Consulta: ver seccion `3.6 Revision inicial de problemas de calidad de datos` en el archivo SQL.

Resultado:

| taxi_type | rows | null_passenger_count | non_positive_passengers | negative_distance | zero_distance | negative_total | dropoff_before_pickup |
|---|---:|---:|---:|---:|---:|---:|---:|
| green | 337114 | 48775 | 4527 | 0 | 12212 | 1023 | 5 |
| yellow | 29703355 | 7716688 | 91359 | 0 | 952231 | 161835 | 10 |

Decision: se deben tratar con cuidado los viajes con pasajeros nulos o no positivos, distancias en cero, montos negativos y viajes con hora de llegada anterior a la salida. No se eliminaron registros en esta fase porque el objetivo era exploratorio.

### Rango temporal

Objetivo: revisar si todos los registros pertenecen al anio esperado.

Consulta: ver seccion `3.6 Rango temporal y registros fuera del anio esperado` en el archivo SQL.

Resultado:

| taxi_type | min_pickup | max_pickup | pickups_outside_2026 |
|---|---|---|---:|
| green | 2008-12-31 17:35:31 | 2026-08-31 23:58:28 | 14 |
| yellow | 2001-01-01 09:23:58 | 2026-08-31 23:59:59 | 17 |

Decision: existen pocos registros con fechas fuera de 2026. En analisis temporal posterior se deberia filtrar por `YEAR(pickup_datetime) = 2026` cuando la pregunta se refiera estrictamente al comportamiento de 2026.

## Que significa consultar directamente Parquet

Consultar directamente un archivo Parquet significa que DuckDB lee los archivos desde el sistema de archivos usando funciones como `read_parquet`, sin cargar previamente los datos a una tabla interna. Esta estrategia es util para volumenes grandes porque Parquet es columnar: DuckDB puede leer solo las columnas necesarias y aprovechar metadatos del archivo para reducir trabajo. Tambien permite incorporar nuevos archivos al flujo simplemente agregandolos al directorio esperado y usando patrones como `*.parquet`.

La principal limitacion observada es que cuando existen diferencias de esquema entre fuentes, como los nombres de fechas de taxis amarillos y verdes, las consultas conjuntas requieren normalizacion explicita.
