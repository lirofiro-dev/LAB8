-- CC3084 - Laboratorio 8 - Ejercicio 3
-- Consultas directas sobre archivos Parquet usando DuckDB.
-- Ejecutar dentro del contenedor lab:
--   docker compose exec lab python -c "import duckdb; con=duckdb.connect(); print(con.execute(open('/workspace/sql/exercise3_direct_parquet_exploration.sql').read()).fetchall())"
--
-- Nota: este archivo documenta las consultas usadas. Para revisar resultados de
-- consultas individuales, ejecutarlas una por una desde DuckDB, Python o Jupyter.

-- 3.1 Cantidad de archivos disponibles por tipo de taxi.
SELECT taxi_type, COUNT(DISTINCT filename) AS files
FROM (
    SELECT 'yellow' AS taxi_type, filename
    FROM read_parquet('/workspace/data/raw/yellow/2026/*.parquet', filename = true)
    UNION ALL
    SELECT 'green' AS taxi_type, filename
    FROM read_parquet('/workspace/data/raw/green/2026/*.parquet', filename = true)
)
GROUP BY taxi_type
ORDER BY taxi_type;

-- 3.1 Meses disponibles por tipo de taxi.
SELECT taxi_type, month, COUNT(*) AS files
FROM (
    SELECT 'yellow' AS taxi_type,
           regexp_extract(filename, '(\\d{4}-\\d{2})', 1) AS month
    FROM (
        SELECT DISTINCT filename
        FROM read_parquet('/workspace/data/raw/yellow/2026/*.parquet', filename = true)
    )
    UNION ALL
    SELECT 'green' AS taxi_type,
           regexp_extract(filename, '(\\d{4}-\\d{2})', 1) AS month
    FROM (
        SELECT DISTINCT filename
        FROM read_parquet('/workspace/data/raw/green/2026/*.parquet', filename = true)
    )
)
GROUP BY taxi_type, month
ORDER BY taxi_type, month;

-- 3.2 Cantidad de registros disponibles.
SELECT 'yellow' AS taxi_type, COUNT(*) AS rows
FROM read_parquet('/workspace/data/raw/yellow/2026/*.parquet')
UNION ALL
SELECT 'green' AS taxi_type, COUNT(*) AS rows
FROM read_parquet('/workspace/data/raw/green/2026/*.parquet')
ORDER BY taxi_type;

-- 3.3 y 3.4 Columnas y tipos de datos para taxis amarillos.
DESCRIBE SELECT *
FROM read_parquet('/workspace/data/raw/yellow/2026/*.parquet');

-- 3.3 y 3.4 Columnas y tipos de datos para taxis verdes.
DESCRIBE SELECT *
FROM read_parquet('/workspace/data/raw/green/2026/*.parquet');

-- 3.5 Muestra de registros de taxis amarillos.
SELECT 'yellow' AS taxi_type,
       VendorID,
       tpep_pickup_datetime AS pickup_datetime,
       tpep_dropoff_datetime AS dropoff_datetime,
       passenger_count,
       trip_distance,
       total_amount,
       payment_type
FROM read_parquet('/workspace/data/raw/yellow/2026/*.parquet')
LIMIT 10;

-- 3.5 Muestra de registros de taxis verdes.
SELECT 'green' AS taxi_type,
       VendorID,
       lpep_pickup_datetime AS pickup_datetime,
       lpep_dropoff_datetime AS dropoff_datetime,
       passenger_count,
       trip_distance,
       total_amount,
       payment_type
FROM read_parquet('/workspace/data/raw/green/2026/*.parquet')
LIMIT 10;

-- 3.6 Revision inicial de problemas de calidad de datos.
SELECT 'yellow' AS taxi_type,
       COUNT(*) AS rows,
       SUM(passenger_count IS NULL) AS null_passenger_count,
       SUM(passenger_count <= 0) AS non_positive_passengers,
       SUM(trip_distance < 0) AS negative_distance,
       SUM(trip_distance = 0) AS zero_distance,
       SUM(total_amount < 0) AS negative_total,
       SUM(tpep_dropoff_datetime < tpep_pickup_datetime) AS dropoff_before_pickup
FROM read_parquet('/workspace/data/raw/yellow/2026/*.parquet')
UNION ALL
SELECT 'green' AS taxi_type,
       COUNT(*) AS rows,
       SUM(passenger_count IS NULL) AS null_passenger_count,
       SUM(passenger_count <= 0) AS non_positive_passengers,
       SUM(trip_distance < 0) AS negative_distance,
       SUM(trip_distance = 0) AS zero_distance,
       SUM(total_amount < 0) AS negative_total,
       SUM(lpep_dropoff_datetime < lpep_pickup_datetime) AS dropoff_before_pickup
FROM read_parquet('/workspace/data/raw/green/2026/*.parquet')
ORDER BY taxi_type;

-- 3.6 Rango temporal y registros fuera del anio esperado.
SELECT 'yellow' AS taxi_type,
       MIN(tpep_pickup_datetime) AS min_pickup,
       MAX(tpep_pickup_datetime) AS max_pickup,
       SUM(YEAR(tpep_pickup_datetime) <> 2026) AS pickups_outside_2026
FROM read_parquet('/workspace/data/raw/yellow/2026/*.parquet')
UNION ALL
SELECT 'green' AS taxi_type,
       MIN(lpep_pickup_datetime) AS min_pickup,
       MAX(lpep_pickup_datetime) AS max_pickup,
       SUM(YEAR(lpep_pickup_datetime) <> 2026) AS pickups_outside_2026
FROM read_parquet('/workspace/data/raw/green/2026/*.parquet')
ORDER BY taxi_type;
