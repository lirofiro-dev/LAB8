"""
CC3084 - Laboratorio 8 - Ejercicio 7

Crea en Metabase el tablero "Lab 8 - Indicadores TLC" usando la API REST.

Requisitos:
  - haber ejecutado scripts/benchmark_parquet_vs_duckdb.py, que crea la base
    /workspace/data/processed/lab8.duckdb con la tabla materializada `trips`;
  - que ningun otro proceso tenga abierta esa base en modo escritura.

Uso (desde el contenedor lab):
  python scripts/setup_metabase.py

Variables opcionales: MB_URL, MB_EMAIL, MB_PASSWORD. El usuario administrador
solo existe en la instancia local de Metabase levantada por docker compose.
"""

from __future__ import annotations

import os
import sys
import time

import requests

MB_URL = os.environ.get("MB_URL", "http://metabase:3000")
MB_EMAIL = os.environ.get("MB_EMAIL", "lab8@example.com")
MB_PASSWORD = os.environ.get("MB_PASSWORD", "Lab8-DuckDB-2026")
DB_FILE = "/workspace/data/processed/lab8.duckdb"
DB_NAME = "Lab8 DuckDB"
DASHBOARD_NAME = "Lab 8 - Indicadores TLC"

# Filtro comun: solo viajes cuyo pickup pertenece al anio del archivo.
BASE = "FROM trips WHERE YEAR(pickup_datetime) = file_year"

# (nombre, display, sql, dimensiones, metricas, ancho, alto)
CARDS = [
    (
        "1. Volumen mensual de viajes",
        "line",
        f"""SELECT strftime(pickup_datetime, '%Y-%m') AS month, taxi_type, COUNT(*) AS trips
{BASE} GROUP BY month, taxi_type ORDER BY month""",
        ["month", "taxi_type"], ["trips"], 12, 6,
    ),
    (
        "2. Monto promedio mensual por viaje",
        "line",
        f"""SELECT strftime(pickup_datetime, '%Y-%m') AS month, taxi_type,
       ROUND(AVG(total_amount), 2) AS avg_total_amount
{BASE} GROUP BY month, taxi_type ORDER BY month""",
        ["month", "taxi_type"], ["avg_total_amount"], 12, 6,
    ),
    (
        "3. Actividad por hora del dia",
        "line",
        f"""SELECT EXTRACT(hour FROM pickup_datetime) AS pickup_hour,
       taxi_type || ' ' || file_year AS serie, COUNT(*) AS trips
{BASE} GROUP BY pickup_hour, serie ORDER BY pickup_hour""",
        ["pickup_hour", "serie"], ["trips"], 12, 6,
    ),
    (
        "4. Distribucion de formas de pago (%)",
        "bar",
        f"""SELECT taxi_type || ' ' || file_year AS serie,
       CASE payment_type WHEN 1 THEN '1 tarjeta' WHEN 2 THEN '2 efectivo'
            WHEN 3 THEN '3 sin cargo' WHEN 4 THEN '4 disputa'
            ELSE 'otro / desconocido' END AS forma_pago,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY taxi_type, file_year), 2) AS pct_trips
{BASE} GROUP BY serie, forma_pago, taxi_type, file_year ORDER BY serie""",
        ["serie", "forma_pago"], ["pct_trips"], 12, 6,
    ),
    (
        "5. Perfil mediano del viaje",
        "table",
        f"""SELECT taxi_type, file_year::VARCHAR AS anio, COUNT(*) AS trips,
       ROUND(median(trip_distance), 2) AS median_distance,
       ROUND(median(duration_minutes), 2) AS median_duration_min,
       ROUND(median(total_amount), 2) AS median_total_amount
{BASE} AND duration_minutes >= 0 GROUP BY taxi_type, file_year ORDER BY taxi_type, file_year""",
        [], [], 12, 5,
    ),
    (
        "6. Propina promedio con tarjeta",
        "bar",
        f"""SELECT taxi_type || ' ' || file_year AS serie, ROUND(AVG(tip_amount), 2) AS avg_tip
{BASE} AND payment_type = 1 AND total_amount > 0 GROUP BY serie ORDER BY serie""",
        ["serie"], ["avg_tip"], 12, 5,
    ),
    (
        "7. Tasas de inconsistencias (%)",
        "bar",
        f"""SELECT taxi_type || ' ' || file_year AS serie,
       ROUND(100.0 * SUM(trip_distance = 0) / COUNT(*), 2) AS pct_zero_distance,
       ROUND(100.0 * SUM(total_amount < 0) / COUNT(*), 2) AS pct_negative_total,
       ROUND(100.0 * SUM(duration_minutes > 240) / COUNT(*), 2) AS pct_duration_over_4h
{BASE} GROUP BY serie ORDER BY serie""",
        ["serie"], ["pct_zero_distance", "pct_negative_total", "pct_duration_over_4h"], 12, 6,
    ),
    (
        "8. Top 10 zonas de origen",
        "table",
        f"""SELECT taxi_type, file_year::VARCHAR AS anio, PULocationID, COUNT(*) AS trips
{BASE} GROUP BY taxi_type, file_year, PULocationID
QUALIFY ROW_NUMBER() OVER (PARTITION BY taxi_type, file_year ORDER BY COUNT(*) DESC) <= 10
ORDER BY taxi_type, file_year, trips DESC""",
        [], [], 12, 6,
    ),
]


def wait_for_metabase(session: requests.Session) -> dict:
    for _ in range(120):
        try:
            r = session.get(f"{MB_URL}/api/session/properties", timeout=5)
            if r.ok:
                return r.json()
        except requests.ConnectionError:
            pass
        time.sleep(5)
    raise SystemExit(f"Metabase no responde en {MB_URL}")


def login(session: requests.Session) -> None:
    props = wait_for_metabase(session)
    token = props.get("setup-token")
    if token and not props.get("has-user-setup"):
        print("Configurando usuario administrador inicial")
        r = session.post(
            f"{MB_URL}/api/setup",
            json={
                "token": token,
                "user": {
                    "email": MB_EMAIL,
                    "password": MB_PASSWORD,
                    "first_name": "Lab",
                    "last_name": "Ocho",
                    "site_name": "Lab 8 DuckDB",
                },
                "prefs": {"site_name": "Lab 8 DuckDB", "allow_tracking": False},
            },
        )
        r.raise_for_status()
    r = session.post(f"{MB_URL}/api/session", json={"username": MB_EMAIL, "password": MB_PASSWORD})
    r.raise_for_status()
    session.headers["X-Metabase-Session"] = r.json()["id"]


def get_or_create_database(session: requests.Session) -> int:
    dbs = session.get(f"{MB_URL}/api/database").json()
    for db in dbs.get("data", dbs if isinstance(dbs, list) else []):
        if db["name"] == DB_NAME:
            return db["id"]
    print("Registrando base DuckDB", DB_FILE)
    r = session.post(
        f"{MB_URL}/api/database",
        json={
            "engine": "duckdb",
            "name": DB_NAME,
            # read_only evita bloquear el archivo para el contenedor lab.
            "details": {"database_file": DB_FILE, "read_only": True},
        },
    )
    if not r.ok:
        raise SystemExit(f"No se pudo registrar la base: {r.status_code} {r.text}")
    return r.json()["id"]


def create_dashboard(session: requests.Session, db_id: int) -> int:
    for d in session.get(f"{MB_URL}/api/dashboard").json():
        if d["name"] == DASHBOARD_NAME:
            print("El tablero ya existe; se elimina para recrearlo")
            session.delete(f"{MB_URL}/api/dashboard/{d['id']}")
    names = {c[0] for c in CARDS}
    for c in session.get(f"{MB_URL}/api/card").json():
        if c["name"] in names:
            session.delete(f"{MB_URL}/api/card/{c['id']}")

    dash_id = session.post(
        f"{MB_URL}/api/dashboard",
        json={
            "name": DASHBOARD_NAME,
            "description": "Indicadores de viajes yellow y green 2024-2026 desde la tabla DuckDB `trips`.",
        },
    ).json()["id"]

    dashcards = []
    row = col = 0
    for i, (name, display, sql, dims, metrics, width, height) in enumerate(CARDS):
        settings = {"graph.dimensions": dims, "graph.metrics": metrics} if dims else {}
        r = session.post(
            f"{MB_URL}/api/card",
            json={
                "name": name,
                "display": display,
                "dataset_query": {"type": "native", "native": {"query": sql}, "database": db_id},
                "visualization_settings": settings,
            },
        )
        r.raise_for_status()
        card_id = r.json()["id"]
        print(f"  tarjeta creada: {name}")
        dashcards.append(
            {"id": -(i + 1), "card_id": card_id, "row": row, "col": col, "size_x": width, "size_y": height}
        )
        # Dos tarjetas por fila en una cuadricula de 24 columnas.
        col = 12 if col == 0 else 0
        if col == 0:
            row += max(height, dashcards[-2]["size_y"])

    r = session.put(f"{MB_URL}/api/dashboard/{dash_id}", json={"dashcards": dashcards})
    r.raise_for_status()
    return dash_id


def main() -> int:
    session = requests.Session()
    login(session)
    db_id = get_or_create_database(session)
    dash_id = create_dashboard(session, db_id)
    print(f"Tablero disponible en http://127.0.0.1:3000/dashboard/{dash_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
