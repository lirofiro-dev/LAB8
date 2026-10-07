# Ejercicio 8 - Incorporacion de 2025 y analisis completo

Este ejercicio amplia el flujo para trabajar con taxis amarillos y verdes de 2024, 2025 y 2026.

## Cambios realizados

- `scripts/download_data.py` ahora incluye por defecto los anios `2024`, `2025` y `2026`.
- Las rutas siguen la estructura `data/raw/<tipo>/<anio>/`.
- El script conserva el comportamiento incremental: si un archivo existe localmente y tiene tamano mayor que cero, no se descarga nuevamente.
- Las consultas usan patrones `**/*.parquet` para incorporar automaticamente nuevos anios.
- Unico cambio necesario en consultas previas: `sql/exercise5_incremental_2024_validation.sql`
  extraia el anio con `regexp_extract(filename, '/(2024|2026)/', 1)`. Con 2025 presente, esa
  expresion devolvia `''` para los archivos de 2025 y la conversion a `INTEGER` fallaba. Se
  reemplazo por el patron generico `'/(\d{4})/'`, el mismo que usan los ejercicios 6, 7 y 8, y la
  consulta conserva su filtro `file_year IN (2024, 2026)` porque valida especificamente esos anios.
  Las consultas de los ejercicios 3, 4, 7 y 8 se ejecutaron sobre los tres anios sin cambios.

## Comando de descarga

```bash
docker compose exec lab python scripts/download_data.py --years 2024 2025 2026
```

Tambien puede usarse el valor por defecto:

```bash
docker compose exec lab python scripts/download_data.py
```

## Resultado de la descarga incremental

Al ejecutar el comando con `--years 2024 2025 2026` sobre el estado local que ya contenia 2026:

- 48 archivos nuevos descargados para 2024 y 2025.
- 16 archivos de 2026 omitidos porque ya existian.
- 8 archivos de 2026 no publicados por la TLC al momento de la ejecucion.
- 0 archivos fallidos.

Una segunda ejecucion valido el comportamiento incremental:

- 0 archivos descargados.
- 64 archivos omitidos porque ya existian.
- 8 archivos de 2026 no publicados.
- 0 archivos fallidos.

Archivos locales disponibles despues de la incorporacion:

| taxi_type | anio | archivos |
|---|---:|---:|
| green | 2024 | 12 |
| green | 2025 | 12 |
| green | 2026 | 8 |
| yellow | 2024 | 12 |
| yellow | 2025 | 12 |
| yellow | 2026 | 8 |

Total: 64 archivos Parquet locales.

## Consultas de validacion

Archivo SQL asociado:

```text
sql/exercise8_full_2024_2025_2026_analysis.sql
```

Las consultas validan:

1. archivos y filas por tipo de taxi y anio;
2. consulta conjunta de 2024, 2025 y 2026;
3. volumen mensual actualizado;
4. evolucion anual de viajes, montos, distancias, duraciones y calidad;
5. cambios porcentuales anuales;
6. horas de mayor actividad por tipo de taxi y anio.

Los resultados obtenidos despues de ejecutar la descarga y las consultas estan en:

```text
docs/exercise8_results.md
```

## Actualizacion de indicadores

El script del Ejercicio 7 (`scripts/generate_indicators.py`) no necesita cambios adicionales,
porque lee todos los Parquet disponibles con patrones recursivos. Despues de descargar 2025,
se regenera el tablero con:

```bash
docker compose exec lab python scripts/generate_indicators.py
```

## Patrones analizados

Al considerar 2024, 2025 y 2026 de manera conjunta, se documentaron estos cambios en
`docs/exercise8_results.md`:

1. evolucion del volumen anual por tipo de taxi;
2. cambios en el monto promedio y mediano por viaje;
3. estabilidad o cambio de las horas de mayor actividad;
4. diferencias en el uso de pagos con tarjeta;
5. variacion en las tasas de inconsistencias como distancia cero o montos negativos.

## Nota de reproducibilidad

Los datos descargados no se versionan en Git. Para reproducir este ejercicio desde cero, basta
con levantar Docker, ejecutar el script de descarga y luego ejecutar las consultas SQL o el script
de indicadores.
