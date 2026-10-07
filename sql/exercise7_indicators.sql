-- CC3084 - Laboratorio 8 - Ejercicio 7
-- Indicadores para tablero de analisis de viajes de taxi.
--
-- Las consultas leen directamente los Parquet disponibles en data/raw y
-- normalizan columnas comunes entre taxis amarillos y verdes.

CREATE OR REPLACE TEMP VIEW trips_available AS
SELECT 'yellow' AS taxi_type,
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

-- Indicador 1: volumen mensual de viajes por tipo de taxi.
SELECT taxi_type,
       file_year,
       strftime(pickup_datetime, '%Y-%m') AS month,
       COUNT(*) AS trips
FROM trips_available
WHERE YEAR(pickup_datetime) = file_year
GROUP BY taxi_type, file_year, month
ORDER BY file_year, month, taxi_type;

-- Indicador 2: monto promedio mensual por viaje.
SELECT taxi_type,
       file_year,
       strftime(pickup_datetime, '%Y-%m') AS month,
       ROUND(AVG(total_amount), 2) AS avg_total_amount,
       ROUND(median(total_amount), 2) AS median_total_amount
FROM trips_available
WHERE YEAR(pickup_datetime) = file_year
GROUP BY taxi_type, file_year, month
ORDER BY file_year, month, taxi_type;

-- Indicador 3: horas con mayor actividad.
SELECT taxi_type,
       file_year,
       EXTRACT(hour FROM pickup_datetime) AS pickup_hour,
       COUNT(*) AS trips
FROM trips_available
WHERE YEAR(pickup_datetime) = file_year
GROUP BY taxi_type, file_year, pickup_hour
ORDER BY file_year, taxi_type, pickup_hour;

-- Indicador 4: distribucion de formas de pago.
SELECT taxi_type,
       file_year,
       payment_type,
       COUNT(*) AS trips,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY taxi_type, file_year), 2) AS pct_trips
FROM trips_available
WHERE YEAR(pickup_datetime) = file_year
GROUP BY taxi_type, file_year, payment_type
ORDER BY file_year, taxi_type, trips DESC;

-- Indicador 5: perfil tipico de distancia, duracion y monto.
SELECT taxi_type,
       file_year,
       COUNT(*) AS trips,
       ROUND(median(trip_distance), 2) AS median_distance,
       ROUND(median(duration_minutes), 2) AS median_duration_min,
       ROUND(median(total_amount), 2) AS median_total_amount,
       ROUND(AVG(trip_distance), 2) AS avg_distance,
       ROUND(AVG(duration_minutes), 2) AS avg_duration_min,
       ROUND(AVG(total_amount), 2) AS avg_total_amount
FROM trips_available
WHERE YEAR(pickup_datetime) = file_year
  AND duration_minutes >= 0
GROUP BY taxi_type, file_year
ORDER BY file_year, taxi_type;

-- Indicador 6: comportamiento de propinas en pagos con tarjeta.
SELECT taxi_type,
       file_year,
       COUNT(*) AS card_trips,
       ROUND(AVG(tip_amount), 2) AS avg_tip,
       ROUND(median(tip_amount), 2) AS median_tip,
       ROUND(AVG(CASE WHEN fare_amount > 0 THEN tip_amount / fare_amount ELSE NULL END), 3) AS avg_tip_to_fare_ratio
FROM trips_available
WHERE YEAR(pickup_datetime) = file_year
  AND payment_type = 1
  AND total_amount > 0
GROUP BY taxi_type, file_year
ORDER BY file_year, taxi_type;

-- Indicador 7: tasa de valores atipicos o inconsistencias.
SELECT taxi_type,
       file_year,
       COUNT(*) AS trips,
       ROUND(100.0 * SUM(trip_distance = 0) / COUNT(*), 2) AS pct_zero_distance,
       ROUND(100.0 * SUM(total_amount < 0) / COUNT(*), 2) AS pct_negative_total,
       ROUND(100.0 * SUM(duration_minutes < 0) / COUNT(*), 4) AS pct_negative_duration,
       ROUND(100.0 * SUM(duration_minutes > 240) / COUNT(*), 2) AS pct_duration_over_4h,
       ROUND(100.0 * SUM(trip_distance > 100) / COUNT(*), 4) AS pct_distance_over_100_miles,
       ROUND(100.0 * SUM(total_amount > 500) / COUNT(*), 4) AS pct_total_over_500
FROM trips_available
WHERE YEAR(pickup_datetime) = file_year
GROUP BY taxi_type, file_year
ORDER BY file_year, taxi_type;

-- Indicador 8: zonas de origen con mas viajes.
SELECT taxi_type,
       file_year,
       PULocationID,
       COUNT(*) AS trips
FROM trips_available
WHERE YEAR(pickup_datetime) = file_year
GROUP BY taxi_type, file_year, PULocationID
QUALIFY ROW_NUMBER() OVER (PARTITION BY taxi_type, file_year ORDER BY COUNT(*) DESC) <= 10
ORDER BY file_year, taxi_type, trips DESC;
