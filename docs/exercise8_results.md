# Ejercicio 8 - Resultados 2024, 2025 y 2026

Este documento fue generado despues de incorporar 2025 y volver a ejecutar las consultas sobre todos los Parquet disponibles.

## Archivos incorporados

| taxi_type | file_year | files | rows |
| --- | --- | --- | --- |
| green | 2024 | 12 | 660218 |
| green | 2025 | 12 | 591375 |
| green | 2026 | 8 | 337114 |
| yellow | 2024 | 12 | 41169720 |
| yellow | 2025 | 12 | 48722602 |
| yellow | 2026 | 8 | 29703355 |

Total local: **64 archivos Parquet**.

## Indicadores anuales actualizados

| taxi_type | file_year | trips | avg_total_amount | median_total_amount | avg_distance | median_distance | median_duration_min | pct_card_payment | pct_zero_distance | pct_negative_total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| green | 2024 | 660196 | 24.26 | 19.32 | 17.02 | 1.87 | 12.0 | 68.87 | 5.24 | 0.33 |
| green | 2025 | 591351 | 25.21 | 20.0 | 19.02 | 1.98 | 13.0 | 68.76 | 4.13 | 0.3 |
| green | 2026 | 337095 | 25.49 | 20.46 | 13.35 | 2.07 | 13.0 | 65.26 | 3.62 | 0.3 |
| yellow | 2024 | 41168533 | 27.83 | 21.0 | 4.98 | 1.76 | 13.0 | 73.97 | 1.89 | 1.48 |
| yellow | 2025 | 48721089 | 26.91 | 21.35 | 6.84 | 1.85 | 13.0 | 63.74 | 2.88 | 2.0 |
| yellow | 2026 | 29703330 | 30.07 | 23.58 | 5.55 | 1.86 | 14.0 | 63.77 | 3.21 | 0.54 |

## Cambios porcentuales anuales

| taxi_type | file_year | trips | avg_total_amount | pct_change_trips | pct_change_avg_total |
| --- | --- | --- | --- | --- | --- |
| green | 2024 | 660198 | 24.26 | N/A | N/A |
| green | 2025 | 591354 | 25.21 | -10.43 | 3.88 |
| green | 2026 | 337100 | 25.49 | -43.0 | 1.13 |
| yellow | 2024 | 41169664 | 27.83 | N/A | N/A |
| yellow | 2025 | 48722573 | 26.91 | 18.35 | -3.32 |
| yellow | 2026 | 29703338 | 30.07 | -39.04 | 11.75 |

## Horas principales de actividad

| taxi_type | file_year | pickup_hour | trips |
| --- | --- | --- | --- |
| green | 2024 | 17 | 53585 |
| green | 2024 | 18 | 51352 |
| green | 2024 | 16 | 49414 |
| green | 2025 | 17 | 47122 |
| green | 2025 | 18 | 44410 |
| green | 2025 | 16 | 44287 |
| green | 2026 | 17 | 26233 |
| green | 2026 | 16 | 25328 |
| green | 2026 | 18 | 24714 |
| yellow | 2024 | 18 | 2955735 |
| yellow | 2024 | 17 | 2813259 |
| yellow | 2024 | 19 | 2598187 |
| yellow | 2025 | 18 | 3473209 |
| yellow | 2025 | 17 | 3291155 |
| yellow | 2025 | 19 | 3071607 |
| yellow | 2026 | 18 | 2091003 |
| yellow | 2026 | 17 | 1997781 |
| yellow | 2026 | 19 | 1840897 |

## Patrones observados

1. **El volumen de taxis amarillos aumenta de 2024 a 2025**: pasa de 41,168,533 a 48,721,089 viajes validos. En 2026 hay 29,703,330, pero ese anio solo tiene datos publicados hasta agosto, por lo que no es comparable como anio completo.
2. **Los taxis verdes disminuyen en 2025 frente a 2024**: pasan de 660,196 a 591,351 viajes validos. Esto refuerza la necesidad de analizar `yellow` y `green` por separado.
3. **El monto promedio crece en ambos tipos entre 2024 y 2026**: yellow pasa de 27.83 a 30.07; green pasa de 24.26 a 25.49.
4. **Las horas de mayor actividad se mantienen en la tarde/noche temprana**, especialmente entre 16:00 y 19:00 para ambos tipos de taxi.
5. **Los problemas de calidad permanecen presentes en los tres anios**, principalmente distancias cero y montos negativos. Por eso los indicadores finales conservan metricas de control de calidad.

## Actualizacion del tablero

El script `scripts/generate_indicators.py` fue ejecutado nuevamente despues de descargar 2024 y 2025. Las figuras actualizadas se encuentran en `docs/figures/` y el resumen del tablero esta en `docs/exercise7_dashboard_results.md`.
