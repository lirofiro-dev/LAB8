-- CC3084 - Laboratorio 8 - Ejercicio 4
-- Analisis exploratorio usando DuckDB sobre archivos Parquet 2026.
-- Las consultas leen directamente desde data/raw, sin materializar tablas.

-- Vista comun usada por las consultas del ejercicio.
CREATE OR REPLACE TEMP VIEW trips_2026 AS
SELECT 'yellow' AS taxi_type,
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
FROM read_parquet('/workspace/data/raw/yellow/2026/*.parquet')
WHERE YEAR(tpep_pickup_datetime) = 2026
UNION ALL
SELECT 'green' AS taxi_type,
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
FROM read_parquet('/workspace/data/raw/green/2026/*.parquet')
WHERE YEAR(lpep_pickup_datetime) = 2026;

-- 4.1 Pregunta: como cambia el volumen de viajes por mes y tipo de taxi?
SELECT taxi_type,
       strftime(pickup_datetime, '%Y-%m') AS month,
       COUNT(*) AS trips,
       ROUND(AVG(total_amount), 2) AS avg_total_amount,
       ROUND(AVG(trip_distance), 2) AS avg_trip_distance
FROM trips_2026
GROUP BY taxi_type, month
ORDER BY taxi_type, month;

-- 4.2 Pregunta: cuales son las horas con mayor actividad para cada tipo de taxi?
SELECT taxi_type,
       EXTRACT(hour FROM pickup_datetime) AS pickup_hour,
       COUNT(*) AS trips
FROM trips_2026
GROUP BY taxi_type, pickup_hour
QUALIFY ROW_NUMBER() OVER (PARTITION BY taxi_type ORDER BY COUNT(*) DESC) <= 5
ORDER BY taxi_type, trips DESC;

-- 4.3 Pregunta: cuales son las caracteristicas tipicas de distancia, duracion y monto?
SELECT taxi_type,
       COUNT(*) AS trips,
       ROUND(AVG(trip_distance), 2) AS avg_distance,
       ROUND(median(trip_distance), 2) AS median_distance,
       ROUND(AVG(duration_minutes), 2) AS avg_duration_min,
       ROUND(median(duration_minutes), 2) AS median_duration_min,
       ROUND(AVG(total_amount), 2) AS avg_total,
       ROUND(median(total_amount), 2) AS median_total
FROM trips_2026
WHERE duration_minutes >= 0
GROUP BY taxi_type
ORDER BY taxi_type;

-- 4.4 Pregunta: como se distribuyen los metodos de pago?
SELECT taxi_type,
       payment_type,
       COUNT(*) AS trips,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY taxi_type), 2) AS pct_trips,
       ROUND(AVG(total_amount), 2) AS avg_total,
       ROUND(AVG(tip_amount), 2) AS avg_tip
FROM trips_2026
GROUP BY taxi_type, payment_type
ORDER BY taxi_type, trips DESC;

-- 4.5 Pregunta: como se comportan las propinas en pagos con tarjeta?
SELECT taxi_type,
       COUNT(*) AS card_trips,
       ROUND(AVG(tip_amount), 2) AS avg_tip,
       ROUND(median(tip_amount), 2) AS median_tip,
       ROUND(AVG(CASE WHEN fare_amount > 0 THEN tip_amount / fare_amount ELSE NULL END), 3) AS avg_tip_to_fare_ratio
FROM trips_2026
WHERE payment_type = 1 AND total_amount > 0
GROUP BY taxi_type
ORDER BY taxi_type;

-- 4.6 Pregunta: que valores atipicos o inconsistencias aparecen en variables clave?
SELECT taxi_type,
       COUNT(*) AS trips,
       SUM(trip_distance = 0) AS zero_distance,
       SUM(total_amount < 0) AS negative_total,
       SUM(duration_minutes < 0) AS negative_duration,
       SUM(duration_minutes > 240) AS duration_over_4h,
       SUM(trip_distance > 100) AS distance_over_100_miles,
       SUM(total_amount > 500) AS total_over_500
FROM trips_2026
GROUP BY taxi_type
ORDER BY taxi_type;

-- 4.7 Pregunta: como se distribuyen distancia y monto, y donde empiezan los valores altos?
SELECT taxi_type,
       ROUND(quantile_cont(trip_distance, 0.5), 2) AS distance_p50,
       ROUND(quantile_cont(trip_distance, 0.95), 2) AS distance_p95,
       ROUND(quantile_cont(trip_distance, 0.99), 2) AS distance_p99,
       ROUND(quantile_cont(total_amount, 0.5), 2) AS total_p50,
       ROUND(quantile_cont(total_amount, 0.95), 2) AS total_p95,
       ROUND(quantile_cont(total_amount, 0.99), 2) AS total_p99
FROM trips_2026
GROUP BY taxi_type
ORDER BY taxi_type;
