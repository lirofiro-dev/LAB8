# Ejercicio 7 - Construccion de indicadores y visualizacion

El ejercicio 7 se resuelve con un conjunto reproducible de consultas e imagenes generadas desde DuckDB.

## Archivos asociados

- Consultas SQL: `sql/exercise7_indicators.sql`.
- Script generador: `scripts/generate_indicators.py`.
- Resultados y evidencia: `docs/exercise7_dashboard_results.md`.
- Figuras: `docs/figures/exercise7_*.png`.

## Como reproducir

Desde la raiz del proyecto, con el ambiente Docker activo:

```bash
docker compose exec lab python scripts/generate_indicators.py
```

El script lee los archivos Parquet disponibles en `data/raw/`, genera archivos CSV derivados en
`data/processed/indicators/` y guarda visualizaciones en `docs/figures/`.

## Uso en Metabase

Metabase esta disponible en <http://127.0.0.1:3000>. Para recrear el tablero ahi:

1. Use la base DuckDB generada en el Ejercicio 6: `/workspace/data/processed/lab8.duckdb`.
2. Cree preguntas SQL nativas usando las consultas de `sql/exercise7_indicators.sql`.
3. Seleccione visualizaciones de linea, barras o tablas segun el indicador.
4. Agrupe las visualizaciones en un dashboard llamado `Lab 8 - Indicadores TLC`.

Las imagenes generadas por el script se incluyen como evidencia reproducible del tablero.
