# Import libraries
import pandas as pd
import sqlite3


data = pd.read_csv('voip_billing_raw.csv',dtype=str, keep_default_na=False)
print(data.head(5))

customer_record = data[data["customer_id"] == "1005"]
print(customer_record)

source_count = len(data)
print("CSV source records:",source_count)


conn = sqlite3.connect('telecom_billing.db')
conn.execute(""" 

CREATE TABLE IF NOT EXISTS raw_billing(
    customer_id TEXT,
    subscription_id TEXT,
    plan TEXT,
    monthly_fee TEXT,
    signup_date TEXT,
    status TEXT
);

""")


result = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
tables = result.fetchall()
print(tables)


schema_result = conn.execute("PRAGMA table_info(raw_billing)")
columns = schema_result.fetchall()
print(columns)



# Check how many records exist in the SQLite table
result = conn.execute("SELECT COUNT(*) FROM raw_billing")

# TODO: Extract the count using fetchone()[0]

row_count = result.fetchone()[0]
# TODO: Print the count with a descriptive label
print(row_count)  

if row_count == 0:
    print("Table is empty. Ready to load data")

    data.to_sql(
        name="raw_billing",
        con=conn,
        if_exists="append",
        index=False
    )
else:
    print("Table already contains records. Skipping load")

# Step 24: Retrieve sample billing records

records_result = conn.execute("SELECT * FROM raw_billing LIMIT 5")

records = records_result.fetchall()

print(records)


result = conn.execute("SELECT plan FROM raw_billing WHERE customer_id = '1005'")
records = result.fetchall()
print(records)


result = conn.execute("""
SELECT COUNT(*)
FROM raw_billing
WHERE customer_id = '1005';
""")

customer_count = result.fetchone()[0]
print("Records for customer 1005:", customer_count)

result = conn.execute("""
SELECT customer_id, subscription_id, plan
FROM raw_billing
WHERE customer_id = '1005';
""")

record = result.fetchone()
print("Customer verification:", record)


db_data = pd.read_sql_query("SELECT * FROM raw_billing", conn)
print(db_data.head())

data_matches = data.equals(db_data)
print("CSV and SQLite match:", data_matches)

conn.close()

