# Telecom Billing Data Ingestion Pipeline

A beginner-friendly **Data Engineering project** that ingests synthetic telecommunications subscription and billing records from a CSV file into a local SQLite database, then checks whether the stored data matches the original source.

This repository documents **Exercise 1: Data Ingestion** in my hands-on Data Engineering learning journey.

## Project overview

The project simulates a small telecom billing data pipeline. It preserves the raw source values so they can be cleaned and transformed in a later exercise.

```text
voip_billing_raw.csv
        |
        v
  Python + Pandas
   ingest_data.py
        |
        v
telecom_billing.db
  raw_billing table
        |
        v
  Pandas validation
 (CSV vs. SQLite)
```

## Technologies

- **Python** — pipeline scripting
- **Pandas** — CSV ingestion, DataFrames, and validation
- **SQLite** (Python's built-in `sqlite3` module) — local database storage and SQL queries
- **Git** — version control
- **VS Code** — development environment

## Project files

```text
telecom-data-pipeline/
├── .gitignore
├── README.md
├── ingest_data.py
├── voip_billing_raw.csv
├── ingest_data_commented.py    # Optional annotated learning copy
├── telecom_billing.db          # Generated locally; ignored by Git
└── .venv/                      # Local environment; ignored by Git
```

> `ingest_data_commented.py` is an optional, commented reconstruction of the exercise. It may differ slightly from the original `ingest_data.py`. The database and virtual environment are created locally and should not be committed.

## Sample dataset

The project uses **82 synthetic VoIP billing records** with six fields:

| Column | Description |
| --- | --- |
| `customer_id` | Customer identifier |
| `subscription_id` | Subscription identifier |
| `plan` | Telecom service or subscription plan |
| `monthly_fee` | Monthly subscription charge as originally recorded |
| `signup_date` | Original subscription date value |
| `status` | Original subscription status |

The source intentionally contains inconsistent formatting, such as `R250` versus `450`, `Active` versus `active`, and differing date formats. **Exercise 1 does not clean these values**; it loads them as text into the raw table.

## Getting started

### 1. Open the project

In VS Code, open the `telecom-data-pipeline` folder. Make sure `voip_billing_raw.csv` and `ingest_data.py` are present.

### 2. Create and activate a virtual environment (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If you already have an active `.venv`, you can skip this step.

### 3. Install Pandas

```powershell
python -m pip install pandas
```

The `sqlite3` module is included with standard Python; it does not require a separate pip installation.

### 4. Run the ingestion pipeline

```powershell
python ingest_data.py
```

The script reads the CSV, creates `telecom_billing.db` and the `raw_billing` table if necessary, loads data if the table is empty, and runs verification queries.

## What the pipeline does

1. Reads `voip_billing_raw.csv` with `dtype=str` to retain the raw text values.
2. Counts and previews the source records.
3. Connects to a local SQLite database.
4. Creates `raw_billing` with six `TEXT` columns if the table does not exist.
5. Checks whether the table already contains records.
6. Loads the CSV into the table when it is empty, using `DataFrame.to_sql()`.
7. Runs SQL checks such as `SELECT`, `WHERE`, and `COUNT(*)`.
8. Reads the SQLite table back into a Pandas DataFrame.
9. Compares the source and destination DataFrames with `.equals()`.
10. Closes the database connection.

## Validation results

During Exercise 1, the following results were observed:

| Check | Observed result |
| --- | --- |
| Source CSV records | 82 |
| SQLite records | 82 |
| Customer `1005` records | 1 |
| Customer `1005` plan | `SIP Trunk` |
| `data.equals(db_data)` | `True` |

Example terminal output from the completed exercise:

```text
CSV source records: 82
Table already contains records. Skipping load
Records for customer 1005: 1
Customer verification: ('1005', 'SUB-0005', 'SIP Trunk')
CSV and SQLite match: True
```

**Note:** `.equals()` compares DataFrames in their current row order, including their labels and values. For larger or production pipelines, records should be matched using stable keys or another order-independent validation approach.

## Current limitations

- The pipeline skips ingestion if `raw_billing` is not empty; it does **not** yet support incremental loads, updates, or recovery from partial loads.
- The dataset is intentionally raw and has not been normalized or cleaned.
- The validation is a learning exercise rather than a production-grade data-quality framework.
- The SQLite database is generated locally and excluded from version control.

## Learning outcomes

This exercise provided hands-on practice with CSV ingestion, Pandas DataFrames, SQLite database creation, SQL filtering and aggregation, basic data validation, `.gitignore`, and Git commits.

## Next exercise

**Exercise 2: Data Transformation** will focus on cleaning and standardizing fields such as monthly fees, status labels, plan names, and signup dates, while preserving the original raw data.

## Data privacy

The CSV used in this learning project is **synthetic training data**, not real customer billing information. Do not commit production customer data, credentials, or confidential records to a public repository.
