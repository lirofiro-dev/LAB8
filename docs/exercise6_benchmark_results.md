# Ejercicio 6 - Resultados del benchmark

Archivo generado por `scripts/benchmark_parquet_vs_duckdb.py`.

Base DuckDB materializada: `/workspace/data/processed/lab8.duckdb`.
Resultados CSV: `/workspace/data/processed/exercise6_benchmark_results.csv`.

| nivel de datos | archivos | filas | consulta | estrategia | mediana segundos | filas resultado | repeticiones |
|---|---:|---:|---|---|---:|---:|---:|
| primeros_1_meses_por_anio | 6 | 10309888 | monthly_volume | direct_parquet | 0.7539 | 11 | 3 |
| primeros_1_meses_por_anio | 6 | 10309888 | monthly_volume | duckdb_table | 2.5566 | 11 | 3 |
| primeros_1_meses_por_anio | 6 | 10309888 | trip_statistics | direct_parquet | 1.5444 | 6 | 3 |
| primeros_1_meses_por_anio | 6 | 10309888 | trip_statistics | duckdb_table | 2.0183 | 6 | 3 |
| primeros_1_meses_por_anio | 6 | 10309888 | payment_distribution | direct_parquet | 0.6383 | 33 | 3 |
| primeros_1_meses_por_anio | 6 | 10309888 | payment_distribution | duckdb_table | 2.0848 | 33 | 3 |
| primeros_1_meses_por_anio | 6 | 10309888 | outlier_counts | direct_parquet | 0.7568 | 6 | 3 |
| primeros_1_meses_por_anio | 6 | 10309888 | outlier_counts | duckdb_table | 2.758 | 6 | 3 |
| primeros_4_meses_por_anio | 24 | 43734857 | monthly_volume | direct_parquet | 3.2074 | 29 | 3 |
| primeros_4_meses_por_anio | 24 | 43734857 | monthly_volume | duckdb_table | 4.2995 | 29 | 3 |
| primeros_4_meses_por_anio | 24 | 43734857 | trip_statistics | direct_parquet | 9.1298 | 6 | 3 |
| primeros_4_meses_por_anio | 24 | 43734857 | trip_statistics | duckdb_table | 4.2301 | 6 | 3 |
| primeros_4_meses_por_anio | 24 | 43734857 | payment_distribution | direct_parquet | 2.33 | 34 | 3 |
| primeros_4_meses_por_anio | 24 | 43734857 | payment_distribution | duckdb_table | 2.6274 | 34 | 3 |
| primeros_4_meses_por_anio | 24 | 43734857 | outlier_counts | direct_parquet | 4.0319 | 6 | 3 |
| primeros_4_meses_por_anio | 24 | 43734857 | outlier_counts | duckdb_table | 3.1037 | 6 | 3 |
| primeros_12_meses_por_anio | 64 | 121184384 | monthly_volume | direct_parquet | 6.672 | 64 | 3 |
| primeros_12_meses_por_anio | 64 | 121184384 | monthly_volume | duckdb_table | 6.4665 | 64 | 3 |
| primeros_12_meses_por_anio | 64 | 121184384 | trip_statistics | direct_parquet | 34.1191 | 6 | 3 |
| primeros_12_meses_por_anio | 64 | 121184384 | trip_statistics | duckdb_table | 9.9765 | 6 | 3 |
| primeros_12_meses_por_anio | 64 | 121184384 | payment_distribution | direct_parquet | 4.5732 | 35 | 3 |
| primeros_12_meses_por_anio | 64 | 121184384 | payment_distribution | duckdb_table | 3.2851 | 35 | 3 |
| primeros_12_meses_por_anio | 64 | 121184384 | outlier_counts | direct_parquet | 7.47 | 6 | 3 |
| primeros_12_meses_por_anio | 64 | 121184384 | outlier_counts | duckdb_table | 5.5886 | 6 | 3 |
