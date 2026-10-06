-- CC3084 - Laboratorio 8 - Ejercicio 5
-- Validacion de incorporacion incremental de datos 2024 junto con 2026.

-- 5.5 Verificar archivos disponibles por tipo de taxi y anio del directorio.
WITH files AS (
    SELECT 'yellow' AS taxi_type,
           regexp_extract(filename, '/(2024|2026)/', 1)::INTEGER AS file_year,
           filename
    FROM read_parquet('/workspace/data/raw/yellow/**/*.parquet', filename = true, union_by_name = true)
    UNION ALL
    SELECT 'green' AS taxi_type,
           regexp_extract(filename, '/(2024|2026)/', 1)::INTEGER AS file_year,
           filename
    FROM read_parquet('/workspace/data/raw/green/**/*.parquet', filename = true, union_by_name = true)
)
SELECT taxi_type,
       file_year,
       COUNT(DISTINCT filename) AS files,
       COUNT(*) AS rows
FROM files
WHERE file_year IN (2024, 2026)
GROUP BY taxi_type, file_year
ORDER BY taxi_type, file_year;

-- 5.6 Consultar conjuntamente 2024 y 2026 con una estructura normalizada.
WITH trips AS (
    SELECT 'yellow' AS taxi_type,
           regexp_extract(filename, '/(2024|2026)/', 1)::INTEGER AS file_year,
           tpep_pickup_datetime AS pickup_datetime,
           trip_distance,
           total_amount
    FROM read_parquet('/workspace/data/raw/yellow/**/*.parquet', filename = true, union_by_name = true)
    UNION ALL
    SELECT 'green' AS taxi_type,
           regexp_extract(filename, '/(2024|2026)/', 1)::INTEGER AS file_year,
           lpep_pickup_datetime AS pickup_datetime,
           trip_distance,
           total_amount
    FROM read_parquet('/workspace/data/raw/green/**/*.parquet', filename = true, union_by_name = true)
)
SELECT taxi_type,
       file_year,
       YEAR(pickup_datetime) AS pickup_year,
       COUNT(*) AS rows,
       ROUND(AVG(trip_distance), 2) AS avg_trip_distance,
       ROUND(AVG(total_amount), 2) AS avg_total_amount
FROM trips
WHERE file_year IN (2024, 2026)
  AND YEAR(pickup_datetime) IN (2024, 2026)
GROUP BY taxi_type, file_year, pickup_year
ORDER BY taxi_type, file_year, pickup_year;

-- 5.7 Validar si existen registros cuyo anio de pickup no coincide con el anio del archivo.
WITH trips AS (
    SELECT 'yellow' AS taxi_type,
           regexp_extract(filename, '/(2024|2026)/', 1)::INTEGER AS file_year,
           tpep_pickup_datetime AS pickup_datetime
    FROM read_parquet('/workspace/data/raw/yellow/**/*.parquet', filename = true, union_by_name = true)
    UNION ALL
    SELECT 'green' AS taxi_type,
           regexp_extract(filename, '/(2024|2026)/', 1)::INTEGER AS file_year,
           lpep_pickup_datetime AS pickup_datetime
    FROM read_parquet('/workspace/data/raw/green/**/*.parquet', filename = true, union_by_name = true)
)
SELECT taxi_type,
       file_year,
       YEAR(pickup_datetime) AS pickup_year,
       COUNT(*) AS rows
FROM trips
WHERE file_year IN (2024, 2026)
  AND YEAR(pickup_datetime) <> file_year
GROUP BY taxi_type, file_year, pickup_year
ORDER BY taxi_type, file_year, pickup_year;

-- 5.8 Comparacion mensual conjunta para confirmar que las consultas anteriores pueden ampliarse.
WITH trips AS (
    SELECT 'yellow' AS taxi_type,
           regexp_extract(filename, '/(2024|2026)/', 1)::INTEGER AS file_year,
           tpep_pickup_datetime AS pickup_datetime,
           total_amount
    FROM read_parquet('/workspace/data/raw/yellow/**/*.parquet', filename = true, union_by_name = true)
    UNION ALL
    SELECT 'green' AS taxi_type,
           regexp_extract(filename, '/(2024|2026)/', 1)::INTEGER AS file_year,
           lpep_pickup_datetime AS pickup_datetime,
           total_amount
    FROM read_parquet('/workspace/data/raw/green/**/*.parquet', filename = true, union_by_name = true)
)
SELECT taxi_type,
       file_year,
       strftime(pickup_datetime, '%Y-%m') AS month,
       COUNT(*) AS trips,
       ROUND(AVG(total_amount), 2) AS avg_total_amount
FROM trips
WHERE file_year IN (2024, 2026)
  AND YEAR(pickup_datetime) = file_year
GROUP BY taxi_type, file_year, month
ORDER BY taxi_type, file_year, month;
