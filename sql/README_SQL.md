# SQL Data Quality Checks for Banking Transactions

This SQL module extends the Python-based banking transaction anomaly detection project with structured data quality checks and reporting queries.

## Objective

The goal is to demonstrate how transaction-level banking data can be validated, aggregated, and prepared for analytical reporting using SQL. The focus is on data quality, plausibility checks, anomaly-related reporting, and transparent validation logic.

## Database

The SQL scripts are written for SQLite and use the scored transaction output from the Python pipeline:

```text
outputs/transactions_scored.csv
```

The imported table is:

```text
transactions_scored
```

## Included SQL scripts

| File | Purpose |
|---|---|
| `01_schema.sql` | Creates the SQLite table for scored transaction data |
| `02_data_quality_checks.sql` | Performs completeness, duplicate, plausibility and consistency checks |
| `03_reporting_queries.sql` | Generates portfolio, country, category, customer and anomaly-related reporting views |

## Covered SQL concepts

- Table schema creation
- CSV import into SQLite
- Aggregations with `COUNT`, `SUM`, `AVG`, `MAX`
- `GROUP BY` and `ORDER BY`
- `CASE WHEN` logic for data quality checks
- Common Table Expressions (CTEs)
- Joins between transaction-level data and customer-level aggregates
- Plausibility and consistency checks

## Example checks

The data quality script checks for:

- missing required values
- duplicate transaction IDs
- invalid transaction amounts
- invalid transaction hours
- anomaly rates by merchant category
- anomaly rates by country
- model anomalies without explanations
- consistency between anomaly flags and explanation text

## Example reporting outputs

The reporting script produces:

- total transaction volume
- average and maximum transaction amounts
- anomaly rate across the portfolio
- transaction volume by country
- transaction volume by merchant category
- top customers by transaction volume
- high-value transactions compared to customer-specific averages
- highest anomaly scores

## How to run

Create the database and schema:

```bash
mkdir -p db
sqlite3 db/banking_transactions.db ".read sql/01_schema.sql"
```

Import the scored transactions:

```bash
sqlite3 db/banking_transactions.db ".mode csv" ".import --skip 1 outputs/transactions_scored.csv transactions_scored"
```

Run the data quality checks:

```bash
sqlite3 -header -column db/banking_transactions.db < sql/02_data_quality_checks.sql
```

Run the reporting queries:

```bash
sqlite3 -header -column db/banking_transactions.db < sql/03_reporting_queries.sql
```

Optionally export results:

```bash
mkdir -p outputs/sql
sqlite3 -header -csv db/banking_transactions.db < sql/02_data_quality_checks.sql > outputs/sql/data_quality_results.csv
sqlite3 -header -csv db/banking_transactions.db < sql/03_reporting_queries.sql > outputs/sql/reporting_results.csv
```

## Relevance

This module demonstrates SQL-based validation and reporting on financial transaction data. It is designed to show practical skills in data quality, plausibility checks, aggregation logic and reproducible analysis workflows.
