"""Exercise 1: Telecom billing CSV-to-SQLite ingestion.

Read synthetic VoIP billing records, store them in a raw SQLite table,
and validate that the stored records match the CSV source.

This is a commented reconstruction of the learning exercise, not a
byte-for-byte export of the original local ingest_data.py.
"""

# STEP 1 — Import the libraries used by our pipeline.
# Pandas reads CSV files and lets us compare tabular datasets.
# sqlite3 connects Python to a local SQLite database.
import pandas as pd
import sqlite3


# STEP 2 — Read the source CSV.
# dtype=str keeps every field as text, matching our raw SQLite schema.
# keep_default_na=False avoids converting blank-like text into NaN values.
data = pd.read_csv("voip_billing_raw.csv", dtype=str, keep_default_na=False)

# Count and preview the source records before loading anything.
source_count = len(data)
print("CSV source records:", source_count)
print("First five CSV records:")
print(data.head(5))

# STEP 3 — Inspect one source record when investigating a discrepancy.
# Boolean filtering returns rows whose customer_id is exactly '1005'.
customer_record = data[data["customer_id"] == "1005"]
print("CSV record for customer 1005:")
print(customer_record)

# STEP 4 — Open (or create) the SQLite database.
conn = sqlite3.connect("telecom_billing.db")

try:
    # STEP 5 — Create the raw ingestion table if it does not already exist.
    # All columns are TEXT so the original values can be preserved before
    # cleaning and transformation in a later exercise.
    conn.execute("""
    CREATE TABLE IF NOT EXISTS raw_billing (
        customer_id TEXT,
        subscription_id TEXT,
        plan TEXT,
        monthly_fee TEXT,
        signup_date TEXT,
        status TEXT
    );
    """)

    # STEP 6 — Check that the table exists and inspect its column schema.
    table_result = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    )
    print("Database tables:", table_result.fetchall())

    schema_result = conn.execute("PRAGMA table_info(raw_billing)")
    print("raw_billing schema:", schema_result.fetchall())

    # STEP 7 — Count existing records before loading.
    # Our introductory approach loads only when the table is empty.
    count_result = conn.execute("SELECT COUNT(*) FROM raw_billing")
    row_count = count_result.fetchone()[0]
    print("Existing SQLite records:", row_count)

    if row_count == 0:
        print("Table is empty. Ready to load data")

        # append inserts DataFrame rows into the existing table.
        # index=False prevents the Pandas index from becoming an extra column.
        data.to_sql(
            name="raw_billing",
            con=conn,
            if_exists="append",
            index=False
        )
        conn.commit()
    else:
        print("Table already contains records. Skipping load")

    # STEP 8 — Preview the first five rows stored in SQLite.
    records_result = conn.execute("SELECT * FROM raw_billing LIMIT 5")
    records = records_result.fetchall()
    print("First five SQLite records:", records)

    # STEP 9 — Use WHERE to investigate a specific customer's plan.
    plan_result = conn.execute(
        "SELECT plan FROM raw_billing WHERE customer_id = ?",
        ("1005",)
    )
    print("Customer 1005 plan:", plan_result.fetchall())

    # STEP 10 — Count records for that customer to investigate duplicates.
    customer_count_result = conn.execute(
        "SELECT COUNT(*) FROM raw_billing WHERE customer_id = ?",
        ("1005",)
    )
    customer_count = customer_count_result.fetchone()[0]
    print("Records for customer 1005:", customer_count)

    # STEP 11 — Verify customer ID, subscription ID, and plan together.
    verification_result = conn.execute("""
        SELECT customer_id, subscription_id, plan
        FROM raw_billing
        WHERE customer_id = ?
    """, ("1005",))
    record = verification_result.fetchone()
    print("Customer verification:", record)

    # STEP 12 — Read all SQLite records into a second Pandas DataFrame.
    db_data = pd.read_sql_query("SELECT * FROM raw_billing", conn)
    print("First five SQLite DataFrame records:")
    print(db_data.head())

    # STEP 13 — Compare the source and destination DataFrames.
    # equals() checks values, labels, row positions, and compatible types.
    # It assumes the two DataFrames have the same row order.
    data_matches = data.equals(db_data)
    print("CSV and SQLite match:", data_matches)

    # Provide a clear signal if the full DataFrame comparison fails.
    if not data_matches:
        print("WARNING: Investigate source/destination differences.")

finally:
    # STEP 14 — Close the connection even if an earlier step raises an error.
    conn.close()

# LIMITATION — Skipping the load whenever the table is nonempty does not
# support incremental updates or recover a partially loaded table.
# We will explore more robust loading and transformation patterns later.
