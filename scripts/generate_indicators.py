#!/usr/bin/env python3
"""Genera indicadores y visualizaciones del Ejercicio 7 usando DuckDB."""

from __future__ import annotations

from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
import pandas as pd


RAW_DIR = Path("/workspace/data/raw")
PROCESSED_DIR = Path("/workspace/data/processed/indicators")
FIG_DIR = Path("/workspace/docs/figures")
DOC_PATH = Path("/workspace/docs/exercise7_dashboard_results.md")


VIEW_SQL = """
CREATE OR REPLACE TEMP VIEW trips_available AS
SELECT 'yellow' AS taxi_type,
       regexp_extract(filename, '/(\\d{4})/', 1)::INTEGER AS file_year,
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
       regexp_extract(filename, '/(\\d{4})/', 1)::INTEGER AS file_year,
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
FROM read_parquet('/workspace/data/raw/green/**/*.parquet', filename = true, union_by_name = true)
"""


QUERIES = {
    "monthly_volume": """
        SELECT taxi_type, file_year, strftime(pickup_datetime, '%Y-%m') AS month, COUNT(*) AS trips
        FROM trips_available
        WHERE YEAR(pickup_datetime) = file_year
        GROUP BY taxi_type, file_year, month
        ORDER BY file_year, month, taxi_type
    """,
    "monthly_amount": """
        SELECT taxi_type, file_year, strftime(pickup_datetime, '%Y-%m') AS month,
               ROUND(AVG(total_amount), 2) AS avg_total_amount,
               ROUND(median(total_amount), 2) AS median_total_amount
        FROM trips_available
        WHERE YEAR(pickup_datetime) = file_year
        GROUP BY taxi_type, file_year, month
        ORDER BY file_year, month, taxi_type
    """,
    "hourly_activity": """
        SELECT taxi_type, file_year, EXTRACT(hour FROM pickup_datetime) AS pickup_hour, COUNT(*) AS trips
        FROM trips_available
        WHERE YEAR(pickup_datetime) = file_year
        GROUP BY taxi_type, file_year, pickup_hour
        ORDER BY file_year, taxi_type, pickup_hour
    """,
    "payment_distribution": """
        SELECT taxi_type, file_year, payment_type, COUNT(*) AS trips,
               ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY taxi_type, file_year), 2) AS pct_trips
        FROM trips_available
        WHERE YEAR(pickup_datetime) = file_year
        GROUP BY taxi_type, file_year, payment_type
        ORDER BY file_year, taxi_type, trips DESC
    """,
    "trip_profile": """
        SELECT taxi_type, file_year, COUNT(*) AS trips,
               ROUND(median(trip_distance), 2) AS median_distance,
               ROUND(median(duration_minutes), 2) AS median_duration_min,
               ROUND(median(total_amount), 2) AS median_total_amount,
               ROUND(AVG(trip_distance), 2) AS avg_distance,
               ROUND(AVG(duration_minutes), 2) AS avg_duration_min,
               ROUND(AVG(total_amount), 2) AS avg_total_amount
        FROM trips_available
        WHERE YEAR(pickup_datetime) = file_year AND duration_minutes >= 0
        GROUP BY taxi_type, file_year
        ORDER BY file_year, taxi_type
    """,
    "tips_card": """
        SELECT taxi_type, file_year, COUNT(*) AS card_trips,
               ROUND(AVG(tip_amount), 2) AS avg_tip,
               ROUND(median(tip_amount), 2) AS median_tip,
               ROUND(AVG(CASE WHEN fare_amount > 0 THEN tip_amount / fare_amount ELSE NULL END), 3) AS avg_tip_to_fare_ratio
        FROM trips_available
        WHERE YEAR(pickup_datetime) = file_year AND payment_type = 1 AND total_amount > 0
        GROUP BY taxi_type, file_year
        ORDER BY file_year, taxi_type
    """,
    "outlier_rates": """
        SELECT taxi_type, file_year, COUNT(*) AS trips,
               ROUND(100.0 * SUM(trip_distance = 0) / COUNT(*), 2) AS pct_zero_distance,
               ROUND(100.0 * SUM(total_amount < 0) / COUNT(*), 2) AS pct_negative_total,
               ROUND(100.0 * SUM(duration_minutes < 0) / COUNT(*), 4) AS pct_negative_duration,
               ROUND(100.0 * SUM(duration_minutes > 240) / COUNT(*), 2) AS pct_duration_over_4h,
               ROUND(100.0 * SUM(trip_distance > 100) / COUNT(*), 4) AS pct_distance_over_100_miles,
               ROUND(100.0 * SUM(total_amount > 500) / COUNT(*), 4) AS pct_total_over_500
        FROM trips_available
        WHERE YEAR(pickup_datetime) = file_year
        GROUP BY taxi_type, file_year
        ORDER BY file_year, taxi_type
    """,
    "top_pickup_zones": """
        SELECT taxi_type, file_year, PULocationID, COUNT(*) AS trips
        FROM trips_available
        WHERE YEAR(pickup_datetime) = file_year
        GROUP BY taxi_type, file_year, PULocationID
        QUALIFY ROW_NUMBER() OVER (PARTITION BY taxi_type, file_year ORDER BY COUNT(*) DESC) <= 10
        ORDER BY file_year, taxi_type, trips DESC
    """,
}


def save_fig(path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=140)
    plt.close()


def label(df: pd.DataFrame) -> pd.Series:
    return df["taxi_type"] + " " + df["file_year"].astype(str)


def generate_plots(data: dict[str, pd.DataFrame]) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    monthly = data["monthly_volume"].copy()
    monthly["series"] = label(monthly)
    pivot = monthly.pivot(index="month", columns="series", values="trips")
    pivot.plot(kind="line", marker="o", figsize=(11, 5), title="Volumen mensual de viajes")
    plt.ylabel("viajes")
    plt.xlabel("mes")
    plt.xticks(rotation=45)
    save_fig(FIG_DIR / "exercise7_01_monthly_volume.png")

    amount = data["monthly_amount"].copy()
    amount["series"] = label(amount)
    pivot = amount.pivot(index="month", columns="series", values="avg_total_amount")
    pivot.plot(kind="line", marker="o", figsize=(11, 5), title="Monto promedio mensual por viaje")
    plt.ylabel("USD")
    plt.xlabel("mes")
    plt.xticks(rotation=45)
    save_fig(FIG_DIR / "exercise7_02_monthly_amount.png")

    hourly = data["hourly_activity"].copy()
    hourly["series"] = label(hourly)
    pivot = hourly.pivot(index="pickup_hour", columns="series", values="trips")
    pivot.plot(kind="line", marker="o", figsize=(11, 5), title="Actividad por hora del dia")
    plt.ylabel("viajes")
    plt.xlabel("hora")
    save_fig(FIG_DIR / "exercise7_03_hourly_activity.png")

    payments = data["payment_distribution"].copy()
    payments["series"] = label(payments)
    top = payments[payments["payment_type"].isin([0, 1, 2, 3, 4])]
    pivot = top.pivot_table(index="series", columns="payment_type", values="pct_trips", aggfunc="sum").fillna(0)
    pivot.plot(kind="bar", stacked=True, figsize=(10, 5), title="Distribucion porcentual de formas de pago")
    plt.ylabel("% de viajes")
    plt.xlabel("tipo/anio")
    plt.xticks(rotation=30)
    save_fig(FIG_DIR / "exercise7_04_payment_distribution.png")

    profile = data["trip_profile"].copy()
    profile["series"] = label(profile)
    profile.set_index("series")[["median_distance", "median_duration_min", "median_total_amount"]].plot(
        kind="bar", figsize=(10, 5), title="Perfil mediano del viaje"
    )
    plt.xlabel("tipo/anio")
    plt.xticks(rotation=30)
    save_fig(FIG_DIR / "exercise7_05_trip_profile.png")

    tips = data["tips_card"].copy()
    tips["series"] = label(tips)
    tips.set_index("series")[["avg_tip", "median_tip", "avg_tip_to_fare_ratio"]].plot(
        kind="bar", figsize=(10, 5), title="Propinas en pagos con tarjeta"
    )
    plt.xlabel("tipo/anio")
    plt.xticks(rotation=30)
    save_fig(FIG_DIR / "exercise7_06_tips_card.png")

    outliers = data["outlier_rates"].copy()
    outliers["series"] = label(outliers)
    outliers.set_index("series")[["pct_zero_distance", "pct_negative_total", "pct_duration_over_4h"]].plot(
        kind="bar", figsize=(10, 5), title="Tasas de inconsistencias principales"
    )
    plt.ylabel("% de viajes")
    plt.xlabel("tipo/anio")
    plt.xticks(rotation=30)
    save_fig(FIG_DIR / "exercise7_07_outlier_rates.png")


def markdown_table(df: pd.DataFrame, max_rows: int = 12) -> str:
    limited = df.head(max_rows).copy()
    headers = [str(c) for c in limited.columns]
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for _, row in limited.iterrows():
        values = [str(row[c]) for c in limited.columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_doc(data: dict[str, pd.DataFrame]) -> None:
    monthly = data["monthly_volume"]
    profile = data["trip_profile"]
    payments = data["payment_distribution"]
    tips = data["tips_card"]
    outliers = data["outlier_rates"]

    top_month = monthly.sort_values("trips", ascending=False).iloc[0]
    top_payment = payments.sort_values("trips", ascending=False).iloc[0]

    lines = [
        "# Ejercicio 7 - Indicadores y visualizacion",
        "",
        "Este documento resume los indicadores generados con `scripts/generate_indicators.py`.",
        "Las consultas fuente estan documentadas en `sql/exercise7_indicators.sql`.",
        "",
        "## Preguntas de analisis",
        "",
        "1. Como cambia el volumen de viajes por mes y tipo de taxi?",
        "2. Que tipo de taxi concentra mas viajes?",
        "3. En que horas del dia hay mayor actividad?",
        "4. Como cambia el monto promedio y mediano por mes?",
        "5. Que tan diferente es el viaje tipico entre taxis amarillos y verdes?",
        "6. Que metodos de pago predominan en cada tipo de taxi?",
        "7. Como se comportan las propinas cuando el pago es con tarjeta?",
        "8. Que porcentaje de viajes tiene distancia cero o montos negativos?",
        "9. Que tan frecuentes son viajes extremadamente largos o caros?",
        "10. Cuales son las zonas de origen con mayor volumen de viajes?",
        "",
        "## Indicadores construidos",
        "",
        "| indicador | pregunta que responde | visualizacion |",
        "|---|---|---|",
        "| Volumen mensual de viajes | 1 y 2 | linea temporal |",
        "| Monto promedio mensual | 4 | linea temporal |",
        "| Actividad por hora | 3 | linea por hora |",
        "| Distribucion de pagos | 6 | barras apiladas |",
        "| Perfil mediano del viaje | 5 | barras agrupadas |",
        "| Propinas con tarjeta | 7 | barras agrupadas |",
        "| Tasas de inconsistencias | 8 y 9 | barras agrupadas |",
        "| Top zonas de origen | 10 | tabla |",
        "",
        "## Visualizaciones generadas",
        "",
        "![Volumen mensual](figures/exercise7_01_monthly_volume.png)",
        "",
        "![Monto mensual](figures/exercise7_02_monthly_amount.png)",
        "",
        "![Actividad por hora](figures/exercise7_03_hourly_activity.png)",
        "",
        "![Pagos](figures/exercise7_04_payment_distribution.png)",
        "",
        "![Perfil de viajes](figures/exercise7_05_trip_profile.png)",
        "",
        "![Propinas](figures/exercise7_06_tips_card.png)",
        "",
        "![Inconsistencias](figures/exercise7_07_outlier_rates.png)",
        "",
        "## Resultados principales",
        "",
        f"El mayor volumen mensual observado fue para `{top_month['taxi_type']}` en `{top_month['month']}`, con `{int(top_month['trips']):,}` viajes.",
        f"El metodo de pago mas frecuente por conteo fue `payment_type = {int(top_payment['payment_type'])}` para `{top_payment['taxi_type']}` {int(top_payment['file_year'])}.",
        "",
        "### Perfil tipico de viajes",
        "",
        markdown_table(profile),
        "",
        "### Propinas en pagos con tarjeta",
        "",
        markdown_table(tips),
        "",
        "### Tasas de inconsistencias",
        "",
        markdown_table(outliers),
        "",
        "## Interpretacion y hallazgos",
        "",
        "1. Los taxis amarillos concentran mucho mas volumen que los verdes, por lo que el tablero separa siempre `taxi_type`.",
        "2. La actividad horaria muestra mayor concentracion en la tarde y noche temprana, consistente con patrones urbanos de movilidad.",
        "3. Los pagos con tarjeta dominan en ambos tipos de taxi y permiten analizar propinas de forma mas consistente.",
        "4. La media y la mediana no siempre cuentan la misma historia; por eso el tablero usa medianas para describir el viaje tipico.",
        "5. Existen inconsistencias como distancia cero, montos negativos y duraciones extremas. Estos indicadores deben monitorearse antes de usar los datos para decisiones finales.",
        "",
        "## Evidencia del tablero",
        "",
        "Las imagenes anteriores funcionan como evidencia reproducible del tablero generado desde DuckDB. Tambien pueden recrearse en Metabase usando las consultas de `sql/exercise7_indicators.sql` y la base `data/processed/lab8.duckdb` generada en el Ejercicio 6.",
    ]
    DOC_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parquet_files = list(RAW_DIR.glob("*/*/*.parquet"))
    if not parquet_files:
        raise SystemExit("No hay archivos Parquet en /workspace/data/raw. Ejecute primero scripts/download_data.py")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(VIEW_SQL)

    data: dict[str, pd.DataFrame] = {}
    for name, query in QUERIES.items():
        df = con.execute(query).df()
        data[name] = df
        df.to_csv(PROCESSED_DIR / f"{name}.csv", index=False)
        print(f"{name}: {len(df)} filas")

    generate_plots(data)
    write_doc(data)
    print(f"Visualizaciones: {FIG_DIR}")
    print(f"Documento: {DOC_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
