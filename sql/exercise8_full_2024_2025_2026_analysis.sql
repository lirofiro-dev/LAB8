-- CC3084 - Laboratorio 8 - Ejercicio 8
-- Incorporacion de 2025 y analisis conjunto 2024, 2025 y 2026.

CREATE OR REPLACE TEMP VIEW trips_2024_2026 AS
SELECT 'yellow' AS taxi_type,
       regexp_extract(filename, '/(\d{4})/', 1)::INTEGER AS file_year,
       filename AS source_file,
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
       filename AS source_file,
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

-- 8.2 Verificar archivos descargados por tipo y anio.
SELECT taxi_type,
       file_year,
       COUNT(DISTINCT source_file) AS files,
       COUNT(*) AS rows
FROM trips_2024_2026
WHERE file_year IN (2024, 2025, 2026)
GROUP BY taxi_type, file_year
ORDER BY taxi_type, file_year;

-- 8.3 Validar que las consultas conjuntas siguen funcionando.
SELECT taxi_type,
       file_year,
       YEAR(pickup_datetime) AS pickup_year,
       COUNT(*) AS trips,
       ROUND(AVG(total_amount), 2) AS avg_total_amount,
       ROUND(median(total_amount), 2) AS median_total_amount
FROM trips_2024_2026
WHERE file_year IN (2024, 2025, 2026)
GROUP BY taxi_type, file_year, pickup_year
ORDER BY taxi_type, file_year, pickup_year;

-- 8.4 Indicador actualizado: volumen mensual para los tres anios.
SELECT taxi_type,
       file_year,
       strftime(pickup_datetime, '%Y-%m') AS month,
       COUNT(*) AS trips,
       ROUND(AVG(total_amount), 2) AS avg_total_amount
FROM trips_2024_2026
WHERE file_year IN (2024, 2025, 2026)
  AND YEAR(pickup_datetime) = file_year
GROUP BY taxi_type, file_year, month
ORDER BY taxi_type, file_year, month;

-- 8.5 Evolucion anual de indicadores seleccionados.
SELECT taxi_type,
       file_year,
       COUNT(*) AS trips,
       ROUND(AVG(total_amount), 2) AS avg_total_amount,
       ROUND(median(total_amount), 2) AS median_total_amount,
       ROUND(AVG(trip_distance), 2) AS avg_distance,
       ROUND(median(trip_distance), 2) AS median_distance,
       ROUND(AVG(duration_minutes), 2) AS avg_duration_min,
       ROUND(median(duration_minutes), 2) AS median_duration_min,
       ROUND(100.0 * SUM(payment_type = 1) / COUNT(*), 2) AS pct_card_payment,
       ROUND(100.0 * SUM(trip_distance = 0) / COUNT(*), 2) AS pct_zero_distance,
       ROUND(100.0 * SUM(total_amount < 0) / COUNT(*), 2) AS pct_negative_total
FROM trips_2024_2026
WHERE file_year IN (2024, 2025, 2026)
  AND YEAR(pickup_datetime) = file_year
  AND duration_minutes >= 0
GROUP BY taxi_type, file_year
ORDER BY taxi_type, file_year;

-- 8.6 Cambios porcentuales anuales de volumen y monto promedio.
WITH annual AS (
    SELECT taxi_type,
           file_year,
           COUNT(*) AS trips,
           AVG(total_amount) AS avg_total_amount
    FROM trips_2024_2026
    WHERE file_year IN (2024, 2025, 2026)
      AND YEAR(pickup_datetime) = file_year
    GROUP BY taxi_type, file_year
)
SELECT taxi_type,
       file_year,
       trips,
       ROUND(avg_total_amount, 2) AS avg_total_amount,
       ROUND(100.0 * (trips - LAG(trips) OVER (PARTITION BY taxi_type ORDER BY file_year)) /
             NULLIF(LAG(trips) OVER (PARTITION BY taxi_type ORDER BY file_year), 0), 2) AS pct_change_trips,
       ROUND(100.0 * (avg_total_amount - LAG(avg_total_amount) OVER (PARTITION BY taxi_type ORDER BY file_year)) /
             NULLIF(LAG(avg_total_amount) OVER (PARTITION BY taxi_type ORDER BY file_year), 0), 2) AS pct_change_avg_total
FROM annual
ORDER BY taxi_type, file_year;

-- 8.6 Top horas de actividad por tipo y anio.
SELECT taxi_type,
       file_year,
       EXTRACT(hour FROM pickup_datetime) AS pickup_hour,
       COUNT(*) AS trips
FROM trips_2024_2026
WHERE file_year IN (2024, 2025, 2026)
  AND YEAR(pickup_datetime) = file_year
GROUP BY taxi_type, file_year, pickup_hour
QUALIFY ROW_NUMBER() OVER (PARTITION BY taxi_type, file_year ORDER BY COUNT(*) DESC) <= 5
ORDER BY taxi_type, file_year, trips DESC;
