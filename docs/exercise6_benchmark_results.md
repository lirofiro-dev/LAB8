# Ejercicio 6 - Resultados del benchmark

Archivo generado por `scripts/benchmark_parquet_vs_duckdb.py`.

Base DuckDB materializada: `/workspace/data/processed/lab8.duckdb`.
Resultados CSV: `/workspace/data/processed/exercise6_benchmark_results.csv`.

| nivel de datos | archivos | filas | consulta | estrategia | mediana segundos | filas resultado | repeticiones |
|---|---:|---:|---|---|---:|---:|---:|
| primeros_1_meses_por_anio | 2 | 3765161 | monthly_volume | direct_parquet | 0.1145 | 4 | 3 |
| primeros_1_meses_por_anio | 2 | 3765161 | monthly_volume | duckdb_table | 0.6598 | 4 | 3 |
| primeros_1_meses_por_anio | 2 | 3765161 | trip_statistics | direct_parquet | 0.2859 | 2 | 3 |
| primeros_1_meses_por_anio | 2 | 3765161 | trip_statistics | duckdb_table | 0.2802 | 2 | 3 |
| primeros_1_meses_por_anio | 2 | 3765161 | payment_distribution | direct_parquet | 0.07 | 10 | 3 |
| primeros_1_meses_por_anio | 2 | 3765161 | payment_distribution | duckdb_table | 1.4035 | 10 | 3 |
| primeros_1_meses_por_anio | 2 | 3765161 | outlier_counts | direct_parquet | 0.1078 | 2 | 3 |
| primeros_1_meses_por_anio | 2 | 3765161 | outlier_counts | duckdb_table | 0.4123 | 2 | 3 |
| primeros_4_meses_por_anio | 8 | 15074537 | monthly_volume | direct_parquet | 0.2594 | 10 | 3 |
| primeros_4_meses_por_anio | 8 | 15074537 | monthly_volume | duckdb_table | 0.9038 | 10 | 3 |
| primeros_4_meses_por_anio | 8 | 15074537 | trip_statistics | direct_parquet | 1.1873 | 2 | 3 |
| primeros_4_meses_por_anio | 8 | 15074537 | trip_statistics | duckdb_table | 1.1449 | 2 | 3 |
| primeros_4_meses_por_anio | 8 | 15074537 | payment_distribution | direct_parquet | 0.1637 | 10 | 3 |
| primeros_4_meses_por_anio | 8 | 15074537 | payment_distribution | duckdb_table | 0.7391 | 10 | 3 |
| primeros_4_meses_por_anio | 8 | 15074537 | outlier_counts | direct_parquet | 0.2489 | 2 | 3 |
| primeros_4_meses_por_anio | 8 | 15074537 | outlier_counts | duckdb_table | 0.8011 | 2 | 3 |
| primeros_8_meses_por_anio | 16 | 30040469 | monthly_volume | direct_parquet | 0.5003 | 16 | 3 |
| primeros_8_meses_por_anio | 16 | 30040469 | monthly_volume | duckdb_table | 0.6576 | 16 | 3 |
| primeros_8_meses_por_anio | 16 | 30040469 | trip_statistics | direct_parquet | 2.4989 | 2 | 3 |
| primeros_8_meses_por_anio | 16 | 30040469 | trip_statistics | duckdb_table | 2.2031 | 2 | 3 |
| primeros_8_meses_por_anio | 16 | 30040469 | payment_distribution | direct_parquet | 0.2989 | 11 | 3 |
| primeros_8_meses_por_anio | 16 | 30040469 | payment_distribution | duckdb_table | 0.7596 | 11 | 3 |
| primeros_8_meses_por_anio | 16 | 30040469 | outlier_counts | direct_parquet | 0.4863 | 2 | 3 |
| primeros_8_meses_por_anio | 16 | 30040469 | outlier_counts | duckdb_table | 0.9125 | 2 | 3 |
