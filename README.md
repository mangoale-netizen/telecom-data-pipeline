# Telecom Billing Data Pipeline

A beginner-friendly **Data Engineering ELT (Extract, Load, Transform)** project that ingests **synthetic telecommunications subscription and billing records** from a CSV file into SQLite, profiles the raw data, and creates a standardized Silver table with explicit data-quality flags.

This repository documents two completed hands-on exercises in a Data Engineering learning journey:

- **Exercise 1 — Data Ingestion (Bronze):** Load CSV records into SQLite without cleaning the source values, then validate the ingestion.
- **Exercise 2 — Data Transformation (Silver):** Profile, clean, standardize, flag, deduplicate, and validate the ingested records.

The project follows a **Bronze → Silver → Gold** architecture. **Bronze and Silver are implemented; the Gold layer is planned.**

## Project overview and architecture

The pipeline simulates a small telecom billing system with subscription records for services such as SIP Trunk, Cloud PBX, Microsoft Teams Extension, and WebRTC. It uses synthetic data, not real customer billing information.

```text
       voip_billing_raw.csv
          82 source rows
                 |
                 v
        Python + Pandas
          ingest_data.py
                 |
                 v
      telecom_billing.db (SQLite)
       Bronze: raw_billing
       82 original records
                 |
          Read and profile
                 v
        Python + Pandas
        transform_data.py
      - Normalize values
      - Parse signup dates
      - Add quality flags
      - Remove exact duplicates
                 |
                 v
      telecom_billing.db (SQLite)
       Silver: clean_billing
       80 rows / 10 columns
                 |
                 v
        Gold layer (planned)
       Metrics and reporting
```

**Design principle:** Bronze retains the original ingested values. Silver makes them easier to analyze without silently inventing missing values or discarding problematic fees.

## Technologies

| Technology | Purpose |
| --- | --- |
| **Python** | Ingestion and transformation scripts |
| **Pandas** | CSV ingestion, profiling, cleaning, DataFrames, and validation |
| **SQLite** (`sqlite3`) | Local relational database, Bronze and Silver tables, SQL checks |
| **VS Code** | Development environment |
| **Git / GitHub** | Version control and milestone tracking |

`sqlite3` is included in the Python standard library; it does not require a separate installation.

## Project files

```text
telecom-data-pipeline/
├── .gitignore
├── README.md
├── ingest_data.py               # Exercise 1: CSV -> Bronze
├── transform_data.py            # Exercise 2: Bronze -> Silver
├── voip_billing_raw.csv         # Synthetic training data
├── ingest_data_commented.py     # Optional annotated learning copy
├── telecom_billing.db           # Generated locally; ignored by Git
└── .venv/                       # Local environment; ignored by Git
```

> `ingest_data_commented.py` is an optional, commented reconstruction of the ingestion exercise and may differ slightly from the original `ingest_data.py`. Files shown reflect the exercise structure; optional files may not exist in every local checkout.

## Dataset and source columns

The CSV contains **82 synthetic VoIP billing records** with six source fields:

| Column | Meaning |
| --- | --- |
| `customer_id` | Customer identifier |
| `subscription_id` | Subscription identifier |
| `plan` | Telecom subscription/service plan |
| `monthly_fee` | Monthly charge as originally recorded |
| `signup_date` | Original signup date value |
| `status` | Original subscription status |

The source intentionally contains data-quality problems to practice engineering workflows, including inconsistent capitalization, currency symbols (`R250`), comma separators (`1,200`), extra whitespace, mixed date formats, missing values, negative fees, and duplicate records.

---

## Getting started

### 1. Open the project

Open the `telecom-data-pipeline` folder in VS Code. Ensure the source CSV and Python scripts are present.

### 2. Create and activate a virtual environment (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If an appropriate `.venv` is already active, skip this step.

### 3. Install dependencies

```powershell
python -m pip install pandas
```

### 4. Run Exercise 1: ingestion

```powershell
python ingest_data.py
```

This creates or opens `telecom_billing.db`, creates `raw_billing` if necessary, loads the CSV when the table is empty, and performs ingestion validation.

### 5. Run Exercise 2: transformation

```powershell
python transform_data.py
```

This reads `raw_billing`, profiles and transforms its records, then writes the resulting DataFrame into the SQLite table `clean_billing`.

**Rerun behavior:** The ingestion exercise **skips loading when `raw_billing` is nonempty**. The current Silver load uses `if_exists="replace"`, which **replaces `clean_billing` on rerun**, not `raw_billing`. Verify the database path and table names before running either script against important data.

---

## Exercise 1 — Data Ingestion (Bronze) ✅

**Goal:** Preserve raw source values in SQLite for later inspection and transformation.

The ingestion script:

1. Reads `voip_billing_raw.csv` into Pandas with `dtype=str` to retain raw field representations.
2. Counts and previews source records.
3. Connects to `telecom_billing.db` using Python's `sqlite3` module.
4. Creates `raw_billing` if necessary, with six `TEXT` columns.
5. Checks the existing row count; inserts CSV records if the table is empty using `DataFrame.to_sql()`.
6. Performs SQL `SELECT`, `WHERE`, and `COUNT(*)` checks.
7. Reads saved records back into a Pandas DataFrame.
8. Compares the source and database DataFrames using `.equals()`.
9. Closes the database connection.

### Ingestion validation results

Results observed during Exercise 1:

| Check | Observed result |
| --- | --- |
| Source CSV rows | **82** |
| `raw_billing` SQLite rows | **82** |
| Records for customer `1005` | **1** |
| Plan for customer `1005` | `SIP Trunk` |
| `data.equals(db_data)` | **`True`** |

Example terminal output from the exercise:

```text
CSV source records: 82
Table already contains records. Skipping load
Records for customer 1005: 1
Customer verification: ('1005', 'SUB-0005', 'SIP Trunk')
CSV and SQLite match: True
```

**Validation note:** `.equals()` compares DataFrames including their values, labels, and current row positions. Production ingestion validation should use stable identifiers or other order-independent checks where row order is not guaranteed.

**Current ingestion limitation:** Skipping the load whenever `raw_billing` is nonempty does not support incremental loads, updates, or recovery from a partially completed load.

---

## Exercise 2 — Data Transformation (Silver) ✅

**Goal:** Convert raw billing records into a consistent, validated dataset while preserving Bronze for traceability.

### Step 1 — Profile Bronze data

Before transforming, the raw dataset was profiled at both a dataset-wide and individual-column level. Checks included shape, data types, missing values, duplicate rows and IDs, unusual fees, mixed dates, and inconsistent plan/status names.

Selected findings from the original 82 records:

- **2 exact duplicate rows**, involving subscription IDs `SUB-0008` and `SUB-0024`.
- Fees containing currency symbols, thousands separators, extra spaces, missing values, and negative amounts.
- Dates in multiple formats, plus blank/missing dates and `not available` placeholders.
- Mixed capitalization such as `Active` / `active`, `Cloud PBX` / `cloud pbx`, and `SIP Trunk` / `SIP trunk`.

### Step 2 — Transform data in Pandas

The transformation begins from a copy of Bronze data (`silver_df = bronze_df.copy()`) so operations on the Silver DataFrame do not intentionally modify the original DataFrame.

#### Monthly fees

- Strip leading/trailing spaces.
- Remove `R` currency symbols and comma separators.
- Convert to numeric with `pd.to_numeric(..., errors="coerce")`.
- Keep unknown/missing fees as null and mark `fee_missing = True`.
- **Retain negative numeric fees** but mark `fee_negative = True` for investigation.

#### Signup dates

- Treat `not available` as missing.
- Parse known source formats explicitly:
  - `%Y-%m-%d`, for example `2026-10-01`
  - `%d/%m/%Y`, for example `02/10/2026`
  - `%Y/%m/%d`, for example `2026/10/03`
- Preserve invalid/missing dates as null and mark `date_missing = True`.

**Date-format assumption:** Values like `02/10/2026` are interpreted as **2 October 2026** (`DD/MM/YYYY`). For a real source system, confirm date conventions with the source owner before using that assumption.

#### Subscription statuses

- Normalize to lowercase.
- Validate nonmissing values against `active`, `suspended`, and `cancelled`.
- Retain missing values and mark `status_missing = True`.

#### Subscription plans

- Normalize to lowercase.
- Validate nonmissing values against `cloud pbx`, `sip trunk`, `microsoft teams extension`, and `webrtc`.

#### Duplicate records

- Remove **exact duplicate rows** using `drop_duplicates()`.
- Confirm no duplicate `subscription_id` values remain in this dataset.
- Do **not** automatically remove all records that merely share a customer ID; a customer could legitimately hold multiple subscriptions.

### Step 3 — Save the Silver table

The transformed DataFrame is written to the same SQLite database:

```python
silver_df.to_sql(
    name="clean_billing",
    con=conn,
    if_exists="replace",
    index=False,
)
```

This creates/replaces **only the `clean_billing` table**. The original `raw_billing` table is kept as the Bronze layer.

## Silver data dictionary

The persisted `clean_billing` table has **80 records and 10 columns**:

| Column | SQLite type | Meaning |
| --- | --- | --- |
| `customer_id` | `INTEGER` | Customer identifier |
| `subscription_id` | `TEXT` | Subscription identifier |
| `plan` | `TEXT` | Normalized plan name |
| `monthly_fee` | `REAL` | Numeric fee; nullable and possibly negative |
| `signup_date` | `TIMESTAMP` | Parsed signup date; nullable |
| `status` | `TEXT` | Normalized subscription status; nullable |
| `fee_missing` | `INTEGER` | `1` if monthly fee is missing, else `0` |
| `fee_negative` | `INTEGER` | `1` if monthly fee is negative, else `0` |
| `date_missing` | `INTEGER` | `1` if signup date is missing, else `0` |
| `status_missing` | `INTEGER` | `1` if status is missing, else `0` |

SQLite represents the Pandas Boolean flags as integers (`True` → `1`; `False` → `0`). The table metadata reports column types and constraints; it does not by itself prove that column values are valid.

## Validation results — Bronze and Silver

The following results were observed during the completed exercises:

| Validation | Observed result |
| --- | --- |
| Original source / Bronze records | **82** |
| Silver records after removing exact duplicates | **80** |
| Silver columns | **10** |
| Duplicate Silver subscription IDs | **0** |
| Missing Silver monthly fees | **8** |
| Missing Silver signup dates | **23** |
| Missing Silver statuses | **16** |
| Unexpected nonmissing Silver plan values | **0** |
| Unexpected nonmissing Silver status values | **0** |
| Inconsistent data-quality flags | **0** |
| SQLite `clean_billing` record count | **80** |
| SQLite `raw_billing` record count (rechecked after transformation) | **82** |

The Silver table was also inspected using `PRAGMA table_info(clean_billing)`, confirming the 10 expected columns and their SQLite types.

**Important distinction:** Rechecking that Bronze contains 82 rows confirms its row count was preserved. It does **not**, by itself, prove that every original Bronze value remained unchanged. The full CSV-to-SQLite `.equals()` check was performed during ingestion; a fresh source-to-Bronze comparison can be added as an automated regression test.

### SQL verification examples

Run these with a SQLite client or a Python SQLite cursor:

```sql
-- Bronze record count
SELECT COUNT(*) FROM raw_billing;

-- Silver record count
SELECT COUNT(*) FROM clean_billing;

-- Saved Silver columns and data types
PRAGMA table_info(clean_billing);

-- Missing/negative fee flags
SELECT
    SUM(fee_missing) AS missing_fees,
    SUM(fee_negative) AS negative_fees
FROM clean_billing;

-- Check for repeated subscription IDs in Silver
SELECT subscription_id, COUNT(*) AS occurrences
FROM clean_billing
GROUP BY subscription_id
HAVING COUNT(*) > 1;
```

## Data-quality decisions and limitations

This exercise prioritizes **traceability and explicit flags** over silent correction. Problematic records are not automatically removed solely because a fee, date, or status is missing or a fee is negative. Business rules for excluding, repairing, or reviewing these cases should be defined before downstream financial reporting.

Additional limitations:

- Ingestion is not incremental and skips reloading whenever Bronze already contains rows.
- Silver currently replaces the target table on each run; it does not maintain change history.
- Date parsing assumes the specified input formats and a day-first interpretation for `DD/MM/YYYY` values.
- Duplicate handling removes exact duplicates only; future datasets may require key-based business rules.
- Verification is currently a mixture of manual checks and development-time validation, rather than a dedicated automated test suite.
- Gold metrics, production logging, error handling, and pipeline orchestration are not implemented yet.

## Data privacy and version control

This project uses **synthetic training data**. Do not commit production customer records, credentials, access tokens, confidential VoIP information, or private databases to a public repository.

Example `.gitignore` entries to review:

```gitignore
.venv/
__pycache__/
*.py[cod]
*.db
.env
```

The `.db` file is generated locally and should remain excluded. The synthetic source CSV can be versioned if it contains no sensitive data and is approved for sharing.

Git commits can record meaningful stages such as:

1. Complete CSV-to-Bronze ingestion and verification.
2. Complete Bronze profiling, Silver transformations, quality flags, and SQLite validation.
3. Add automated tests and Gold-layer calculations in later milestones.

## Learning outcomes

**Exercise 1:** CSV ingestion, DataFrame inspection, SQLite connections and table creation, SQL filters and counts, data comparison, virtual environments, and Git basics.

**Exercise 2:** Data profiling, standardization, type conversion, explicit mixed-format date parsing, missing-value and anomaly flags, deduplication, SQL table loading, SQLite schema inspection, and Bronze/Silver validation.

## Roadmap

- [x] **Exercise 1:** Ingest synthetic CSV data into Bronze (`raw_billing`)
- [x] Validate 82 source records against the saved Bronze data
- [x] **Exercise 2:** Profile, transform, and validate Silver data
- [x] Save 80 records / 10 columns to Silver (`clean_billing`)
- [x] Verify Silver table count/schema and recheck Bronze count
- [ ] Add repeatable automated data-quality tests
- [ ] Define **Gold** analytics metrics (e.g., subscription counts and billing/revenue summaries)
- [ ] Build Gold tables and basic reporting/visualization
- [ ] Add incremental loading, configuration, logging, and more robust error handling

---

*This project is a learning portfolio exercise. The data and validation procedures should be reviewed and extended before applying the pipeline to real telecommunications billing systems.*
