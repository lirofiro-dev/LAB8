-- CC3084 - Laboratorio 8 - Ejercicio 6
-- Benchmark conceptual: consultas directas Parquet versus tabla DuckDB.
--
-- El script reproducible que ejecuta estas consultas y registra tiempos es:
--   scripts/benchmark_parquet_vs_duckdb.py
--
-- Las consultas usan una estructura normalizada con columnas comunes entre
-- taxis amarillos y verdes.
--
-- Ejecutar sobre una base en archivo (duckdb.connect('/workspace/data/processed/lab8.duckdb')),
-- no en memoria: con 2024-2026 la tabla tiene ~120 M filas y en memoria excede la RAM del contenedor.

-- 6.2 Crear tabla materializada desde los Parquet disponibles.
-- Esta version muestra el patron general; el script genera dinamicamente las
-- listas exactas de archivos disponibles.
CREATE OR REPLACE TABLE trips AS
SELECT 'yellow' AS taxi_type,
       filename AS source_file,
       regexp_extract(filename, '/(\d{4})/', 1)::INTEGER AS file_year,
       tpep_pickup_datetime AS pickup_datetime,
       tpep_dropoff_datetime AS dropoff_datetime,
       passenger_count,
       trip_distance,
       fare_amount,
       tip_amount,
       tolls_amount,
       total_amount,
       payment_type,
       PULocationID,
       DOLocationID,
       datediff('minute', tpep_pickup_datetime, tpep_dropoff_datetime) AS duration_minutes
FROM read_parquet('/workspace/data/raw/yellow/**/*.parquet', filename = true, union_by_name = true)
UNION ALL
SELECT 'green' AS taxi_type,
       filename AS source_file,
       regexp_extract(filename, '/(\d{4})/', 1)::INTEGER AS file_year,
       lpep_pickup_datetime AS pickup_datetime,
       lpep_dropoff_datetime AS dropoff_datetime,
       passenger_count,
       trip_distance,
       fare_amount,
       tip_amount,
       tolls_amount,
       total_amount,
       payment_type,
       PULocationID,
       DOLocationID,
       datediff('minute', lpep_pickup_datetime, lpep_dropoff_datetime) AS duration_minutes
FROM read_parquet('/workspace/data/raw/green/**/*.parquet', filename = true, union_by_name = true);

CREATE INDEX IF NOT EXISTS idx_trips_source_file ON trips(source_file);
CREATE INDEX IF NOT EXISTS idx_trips_year_type ON trips(file_year, taxi_type);

-- 6.3 Consulta representativa 1: volumen mensual.
SELECT taxi_type,
       file_year,
       strftime(pickup_datetime, '%Y-%m') AS month,
       COUNT(*) AS trips,
       ROUND(AVG(total_amount), 2) AS avg_total
FROM trips
WHERE YEAR(pickup_datetime) = file_year
GROUP BY taxi_type, file_year, month
ORDER BY taxi_type, file_year, month;

-- 6.3 Consulta representativa 2: estadisticas de viajes.
SELECT taxi_type,
       file_year,
       COUNT(*) AS trips,
       ROUND(AVG(trip_distance), 2) AS avg_distance,
       ROUND(median(trip_distance), 2) AS median_distance,
       ROUND(AVG(duration_minutes), 2) AS avg_duration_min,
       ROUND(median(duration_minutes), 2) AS median_duration_min,
       ROUND(AVG(total_amount), 2) AS avg_total,
       ROUND(median(total_amount), 2) AS median_total
FROM trips
WHERE YEAR(pickup_datetime) = file_year
  AND duration_minutes >= 0
GROUP BY taxi_type, file_year
ORDER BY taxi_type, file_year;

-- 6.3 Consulta representativa 3: distribucion de pagos.
SELECT taxi_type,
       file_year,
       payment_type,
       COUNT(*) AS trips,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY taxi_type, file_year), 2) AS pct_trips,
       ROUND(AVG(total_amount), 2) AS avg_total,
       ROUND(AVG(tip_amount), 2) AS avg_tip
FROM trips
WHERE YEAR(pickup_datetime) = file_year
GROUP BY taxi_type, file_year, payment_type
ORDER BY taxi_type, file_year, trips DESC;

-- 6.3 Consulta representativa 4: conteo de valores atipicos.
SELECT taxi_type,
       file_year,
       COUNT(*) AS trips,
       SUM(trip_distance = 0) AS zero_distance,
       SUM(total_amount < 0) AS negative_total,
       SUM(duration_minutes < 0) AS negative_duration,
       SUM(duration_minutes > 240) AS duration_over_4h,
       SUM(trip_distance > 100) AS distance_over_100_miles,
       SUM(total_amount > 500) AS total_over_500
FROM trips
WHERE YEAR(pickup_datetime) = file_year
GROUP BY taxi_type, file_year
ORDER BY taxi_type, file_year;
