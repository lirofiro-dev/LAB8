#!/usr/bin/env python3
"""Benchmark de consultas directas Parquet versus tabla DuckDB.

El script detecta los archivos disponibles en data/raw, crea una tabla
materializada normalizada en data/processed/lab8.duckdb y compara tiempos de
consultas equivalentes sobre:

1. Archivos Parquet consultados directamente con read_parquet.
2. Tabla materializada trips dentro de DuckDB.

Uso dentro del contenedor:
    python scripts/benchmark_parquet_vs_duckdb.py
"""

from __future__ import annotations

import argparse
import csv
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import duckdb


RAW_DIR = Path("/workspace/data/raw")
PROCESSED_DIR = Path("/workspace/data/processed")
DB_PATH = PROCESSED_DIR / "lab8.duckdb"
CSV_PATH = PROCESSED_DIR / "exercise6_benchmark_results.csv"
MD_PATH = Path("/workspace/docs/exercise6_benchmark_results.md")


@dataclass(frozen=True)
class FileInfo:
    taxi_type: str
    year: int
    month: int
    path: Path


def discover_files() -> list[FileInfo]:
    files: list[FileInfo] = []
    for taxi_type in ("yellow", "green"):
        for path in sorted((RAW_DIR / taxi_type).glob("*/*.parquet")):
            # Ejemplo: yellow_tripdata_2026-01.parquet
            stem = path.stem
            try:
                year_month = stem.rsplit("_", 1)[1]
                year_s, month_s = year_month.split("-")
                files.append(FileInfo(taxi_type, int(year_s), int(month_s), path))
            except (IndexError, ValueError):
                continue
    return sorted(files, key=lambda f: (f.year, f.month, f.taxi_type, str(f.path)))


def sql_list(paths: list[Path]) -> str:
    return "[" + ", ".join("'" + str(p).replace("'", "''") + "'" for p in paths) + "]"


def normalized_union_sql(files: list[FileInfo]) -> str:
    yellow_paths = [f.path for f in files if f.taxi_type == "yellow"]
    green_paths = [f.path for f in files if f.taxi_type == "green"]
    parts: list[str] = []

    if yellow_paths:
        parts.append(
            f"""
            SELECT
                'yellow' AS taxi_type,
                filename AS source_file,
                regexp_extract(filename, '/(\\d{{4}})/', 1)::INTEGER AS file_year,
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
            FROM read_parquet({sql_list(yellow_paths)}, filename = true, union_by_name = true)
            """
        )

    if green_paths:
        parts.append(
            f"""
            SELECT
                'green' AS taxi_type,
                filename AS source_file,
                regexp_extract(filename, '/(\\d{{4}})/', 1)::INTEGER AS file_year,
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
            FROM read_parquet({sql_list(green_paths)}, filename = true, union_by_name = true)
            """
        )

    if not parts:
        raise RuntimeError("No se encontraron archivos Parquet en /workspace/data/raw")
    return "\nUNION ALL\n".join(parts)


QUERIES = {
    "monthly_volume": """
        SELECT taxi_type,
               file_year,
               strftime(pickup_datetime, '%Y-%m') AS month,
               COUNT(*) AS trips,
               ROUND(AVG(total_amount), 2) AS avg_total
        FROM {source}
        WHERE YEAR(pickup_datetime) = file_year
        GROUP BY taxi_type, file_year, month
        ORDER BY taxi_type, file_year, month
    """,
    "trip_statistics": """
        SELECT taxi_type,
               file_year,
               COUNT(*) AS trips,
               ROUND(AVG(trip_distance), 2) AS avg_distance,
               ROUND(median(trip_distance), 2) AS median_distance,
               ROUND(AVG(duration_minutes), 2) AS avg_duration_min,
               ROUND(median(duration_minutes), 2) AS median_duration_min,
               ROUND(AVG(total_amount), 2) AS avg_total,
               ROUND(median(total_amount), 2) AS median_total
        FROM {source}
        WHERE YEAR(pickup_datetime) = file_year
          AND duration_minutes >= 0
        GROUP BY taxi_type, file_year
        ORDER BY taxi_type, file_year
    """,
    "payment_distribution": """
        SELECT taxi_type,
               file_year,
               payment_type,
               COUNT(*) AS trips,
               ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY taxi_type, file_year), 2) AS pct_trips,
               ROUND(AVG(total_amount), 2) AS avg_total,
               ROUND(AVG(tip_amount), 2) AS avg_tip
        FROM {source}
        WHERE YEAR(pickup_datetime) = file_year
        GROUP BY taxi_type, file_year, payment_type
        ORDER BY taxi_type, file_year, trips DESC
    """,
    "outlier_counts": """
        SELECT taxi_type,
               file_year,
               COUNT(*) AS trips,
               SUM(trip_distance = 0) AS zero_distance,
               SUM(total_amount < 0) AS negative_total,
               SUM(duration_minutes < 0) AS negative_duration,
               SUM(duration_minutes > 240) AS duration_over_4h,
               SUM(trip_distance > 100) AS distance_over_100_miles,
               SUM(total_amount > 500) AS total_over_500
        FROM {source}
        WHERE YEAR(pickup_datetime) = file_year
        GROUP BY taxi_type, file_year
        ORDER BY taxi_type, file_year
    """,
}


def select_levels(files: list[FileInfo]) -> dict[str, list[FileInfo]]:
    months_by_year: dict[int, list[int]] = defaultdict(list)
    for f in files:
        if f.month not in months_by_year[f.year]:
            months_by_year[f.year].append(f.month)

    levels: dict[str, list[FileInfo]] = {}
    max_months = max(len(m) for m in months_by_year.values())
    candidates = sorted({1, min(4, max_months), max_months})
    for n in candidates:
        selected: list[FileInfo] = []
        for year, months in months_by_year.items():
            allowed = set(sorted(months)[:n])
            selected.extend(f for f in files if f.year == year and f.month in allowed)
        levels[f"primeros_{n}_meses_por_anio"] = sorted(selected, key=lambda f: (f.year, f.month, f.taxi_type))
    return levels


def materialize_table(con: duckdb.DuckDBPyConnection, files: list[FileInfo], force: bool) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    if force:
        con.execute("DROP TABLE IF EXISTS trips")

    exists = con.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'trips'"
    ).fetchone()[0]
    if exists:
        return

    print("Creando tabla materializada trips en", DB_PATH)
    con.execute(f"CREATE TABLE trips AS {normalized_union_sql(files)}")
    con.execute("CREATE INDEX idx_trips_source_file ON trips(source_file)")
    con.execute("CREATE INDEX idx_trips_year_type ON trips(file_year, taxi_type)")


def time_query(con: duckdb.DuckDBPyConnection, query: str, repeats: int) -> tuple[float, int]:
    times: list[float] = []
    row_count = 0
    for _ in range(repeats):
        start = time.perf_counter()
        rows = con.execute(query).fetchall()
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        row_count = len(rows)
    return statistics.median(times), row_count


def run_benchmark(repeats: int, force_materialize: bool) -> list[dict[str, object]]:
    files = discover_files()
    if not files:
        raise SystemExit("No hay archivos Parquet. Ejecute primero scripts/download_data.py")

    print(f"Archivos detectados: {len(files)}")
    by_year_type = defaultdict(int)
    for f in files:
        by_year_type[(f.taxi_type, f.year)] += 1
    for key, count in sorted(by_year_type.items()):
        print(f"  {key[0]} {key[1]}: {count} archivos")

    con = duckdb.connect(str(DB_PATH))
    materialize_table(con, files, force_materialize)

    results: list[dict[str, object]] = []
    for level_name, selected in select_levels(files).items():
        source_files = [str(f.path) for f in selected]
        file_filter = "source_file IN (" + ", ".join("'" + p.replace("'", "''") + "'" for p in source_files) + ")"
        parquet_view_sql = normalized_union_sql(selected)
        parquet_source = f"({parquet_view_sql})"
        table_source = f"(SELECT * FROM trips WHERE {file_filter})"
        approx_rows = con.execute(f"SELECT COUNT(*) FROM {table_source}").fetchone()[0]

        print(f"\nNivel {level_name}: {len(selected)} archivos, {approx_rows:,} filas")
        for query_name, template in QUERIES.items():
            parquet_query = template.format(source=parquet_source)
            table_query = template.format(source=table_source)
            parquet_time, parquet_rows = time_query(con, parquet_query, repeats)
            table_time, table_rows = time_query(con, table_query, repeats)
            results.append(
                {
                    "dataset_level": level_name,
                    "files": len(selected),
                    "rows": approx_rows,
                    "query": query_name,
                    "strategy": "direct_parquet",
                    "median_seconds": round(parquet_time, 4),
                    "result_rows": parquet_rows,
                    "repeats": repeats,
                }
            )
            results.append(
                {
                    "dataset_level": level_name,
                    "files": len(selected),
                    "rows": approx_rows,
                    "query": query_name,
                    "strategy": "duckdb_table",
                    "median_seconds": round(table_time, 4),
                    "result_rows": table_rows,
                    "repeats": repeats,
                }
            )
            print(f"  {query_name}: parquet={parquet_time:.3f}s tabla={table_time:.3f}s")

    return results


def write_outputs(results: list[dict[str, object]]) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    lines = [
        "# Ejercicio 6 - Resultados del benchmark",
        "",
        "Archivo generado por `scripts/benchmark_parquet_vs_duckdb.py`.",
        "",
        f"Base DuckDB materializada: `{DB_PATH}`.",
        f"Resultados CSV: `{CSV_PATH}`.",
        "",
        "| nivel de datos | archivos | filas | consulta | estrategia | mediana segundos | filas resultado | repeticiones |",
        "|---|---:|---:|---|---|---:|---:|---:|",
    ]
    for row in results:
        lines.append(
            "| {dataset_level} | {files} | {rows} | {query} | {strategy} | {median_seconds} | {result_rows} | {repeats} |".format(
                **row
            )
        )
    MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\nResultados escritos en:")
    print(" ", CSV_PATH)
    print(" ", MD_PATH)


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark Parquet vs tabla DuckDB")
    parser.add_argument("--repeats", type=int, default=3, help="repeticiones por consulta")
    parser.add_argument(
        "--force-materialize",
        action="store_true",
        help="recrear la tabla materializada aunque ya exista",
    )
    args = parser.parse_args()

    results = run_benchmark(args.repeats, args.force_materialize)
    write_outputs(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
