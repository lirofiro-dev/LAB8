# Ejercicio 4 - Analisis exploratorio con DuckDB

Este documento registra el analisis exploratorio realizado sobre los datos disponibles de 2026 usando DuckDB directamente sobre archivos Parquet.

Archivo SQL asociado: `sql/exercise4_exploratory_analysis.sql`.

## Preguntas de analisis

1. Como cambia el volumen de viajes por mes y tipo de taxi?
2. Cuales son las horas con mayor actividad para taxis amarillos y verdes?
3. Cuales son las caracteristicas tipicas de distancia, duracion y monto por tipo de taxi?
4. Como se distribuyen los metodos de pago?
5. Como se comportan las propinas en pagos con tarjeta?
6. Que valores atipicos o inconsistencias aparecen en variables clave?
7. Como se distribuyen distancia y monto, y donde empiezan los valores altos?

## Fuente y preparacion logica

Las consultas usan directamente:

- `data/raw/yellow/2026/*.parquet`
- `data/raw/green/2026/*.parquet`

Se creo una vista temporal `trips_2026` para normalizar columnas equivalentes entre taxis amarillos y verdes:

- `tpep_pickup_datetime` y `lpep_pickup_datetime` se normalizan como `pickup_datetime`.
- `tpep_dropoff_datetime` y `lpep_dropoff_datetime` se normalizan como `dropoff_datetime`.
- Se agrega `taxi_type` para distinguir `yellow` y `green`.
- Se calcula `duration_minutes` con la diferencia entre pickup y dropoff.
- Se filtra `YEAR(pickup_datetime) = 2026` para evitar registros con fechas fuera del anio esperado.

## Resultados principales

### Volumen mensual

| taxi_type | mes inicial | mes final | patron observado |
|---|---|---|---|
| green | 2026-01: 40258 viajes | 2026-08: 40678 viajes | Volumen mensual estable, entre 37 mil y 45 mil viajes. |
| yellow | 2026-01: 3724894 viajes | 2026-08: 3336739 viajes | Volumen mucho mayor, con maximo en mayo y descenso hacia agosto. |

Decision: las comparaciones deben hacerse por separado o usando porcentajes, porque el volumen de taxis amarillos domina el total.

### Horas con mayor actividad

| taxi_type | horas con mas viajes |
|---|---|
| green | 17, 16, 18, 15, 14 |
| yellow | 18, 17, 19, 16, 21 |

Interpretacion: ambos servicios concentran actividad en la tarde y tarde-noche. Esto sugiere relacion con horarios de salida de trabajo y actividades nocturnas.

### Caracteristicas de los viajes

| taxi_type | avg_distance | median_distance | avg_duration_min | median_duration_min | avg_total | median_total |
|---|---:|---:|---:|---:|---:|---:|
| green | 13.35 | 2.07 | 20.78 | 13.0 | 25.49 | 20.46 |
| yellow | 5.55 | 1.86 | 17.66 | 14.0 | 30.07 | 23.58 |

Interpretacion: la media de distancia de taxis verdes es mucho mayor que su mediana, lo que indica valores extremos. Las medianas de distancia son similares entre taxis verdes y amarillos, pero el monto mediano es mayor en taxis amarillos.

### Metodos de pago

| taxi_type | payment_type principal | porcentaje |
|---|---:|---:|
| green | 1 | 65.25% |
| yellow | 1 | 63.77% |

Interpretacion: el pago tipo `1`, usualmente tarjeta de credito en la documentacion TLC, es el mas frecuente en ambos tipos de taxi. En taxis amarillos aparece una proporcion alta de `payment_type = 0`, asociada a registros sin clasificacion tradicional o posiblemente viajes reportados por fuentes agregadas.

### Propinas en pagos con tarjeta

| taxi_type | card_trips | avg_tip | median_tip | avg_tip_to_fare_ratio |
|---|---:|---:|---:|---:|
| green | 219837 | 3.84 | 3.08 | 0.256 |
| yellow | 18937396 | 4.28 | 3.29 | 0.254 |

Interpretacion: las propinas promedio y medianas son ligeramente mayores en taxis amarillos, pero la razon propina/tarifa es casi igual en ambos tipos.

### Valores atipicos e inconsistencias

| taxi_type | zero_distance | negative_total | negative_duration | duration_over_4h | distance_over_100_miles | total_over_500 |
|---|---:|---:|---:|---:|---:|---:|
| green | 12208 | 1023 | 5 | 1213 | 72 | 21 |
| yellow | 952231 | 161834 | 8 | 8576 | 1223 | 791 |

Interpretacion: existen viajes con distancia cero, montos negativos, duraciones negativas y valores muy altos. Estos registros deben revisarse antes de construir indicadores finales o modelos.

### Distribucion de distancia y monto

| taxi_type | distance_p50 | distance_p95 | distance_p99 | total_p50 | total_p95 | total_p99 |
|---|---:|---:|---:|---:|---:|---:|
| green | 2.07 | 10.52 | 17.76 | 20.46 | 57.65 | 97.20 |
| yellow | 1.86 | 12.30 | 19.50 | 23.58 | 77.51 | 105.75 |

Interpretacion: el 99% de viajes queda por debajo de 17.76 millas en taxis verdes y 19.50 millas en amarillos. Los viajes por encima de 100 millas son atipicos frente a esta distribucion.

## Hallazgos relevantes

1. Los taxis amarillos tienen un volumen de viajes ampliamente superior al de taxis verdes, por lo que las metricas globales estarian dominadas por yellow si no se separa por `taxi_type`.
2. La actividad se concentra en horas de la tarde y noche temprana para ambos tipos de taxi, especialmente entre 16:00 y 19:00.
3. La media de distancia de taxis verdes esta inflada por valores extremos; la mediana muestra que el viaje tipico verde es cercano al viaje tipico amarillo en distancia.
4. El pago con tarjeta es el metodo dominante en ambos servicios y la razon propina/tarifa es muy similar entre yellow y green.
5. Hay problemas claros de calidad de datos: distancias cero, montos negativos, duraciones negativas y viajes extremadamente largos o caros.

## Decisiones para ejercicios posteriores

- Mantener `taxi_type` en toda consulta conjunta.
- Usar medianas y percentiles ademas de promedios para evitar interpretaciones afectadas por outliers.
- Filtrar `YEAR(pickup_datetime) = 2026` en analisis temporal de 2026.
- Documentar explicitamente si una consulta incluye o excluye registros con montos negativos, distancias cero o duraciones invalidas.
