# Transform Bronze(raw) to Silver(Cleaned) data
import pandas as pd
import  sqlite3

# STEP 1 — EXTRACT Connect to the Bronze SQLite database
conn = sqlite3.connect('telecom_billing.db')

# STEP 2 — LOAD Read raw_billing into bronze_df from the SQLite database
bronze_df = pd.read_sql_query("SELECT * FROM raw_billing", conn)

# STEP 3 — PROFILE BRONZE
# Level 1: Dataset-wide Bronze Profiling

#Level 1 Check 1 Row and column counts
print("number of rows and columns in Bronze dataset:")
print(bronze_df.shape)

#Level 1 Check 2 Missing-value counts
print("missing values in each column:")
print(bronze_df.isnull().sum())
print("Three columns require investigation before the data can be trusted for billing and reporting.")

#Level 1 Check 3 — Exact duplicate rows
print("number of exact duplicate rows in Bronze dataset:")
print(bronze_df.duplicated().sum())

#Level 1 Check 4 — Duplicate subscription IDs
print("number of duplicate subscription IDs in Bronze dataset:")
print(bronze_df["subscription_id"].duplicated().sum())

#Level 1 Check 5 — Data types of each column
print("data types of each column:")
print(bronze_df.dtypes)

#Level 1 Check 6 — Unique Categorical Values
print("unique values in the plan column:")
print(bronze_df["plan"].unique())

print("unique values in the status column:")
print(bronze_df["status"].unique())

print(" ------End of Level 1 Profiling Checks------")


# Level 2: Column-by-column profiling

# Column 1: monthly_fee
# Missing values, currency symbols, commas, invalid numbers

# Check 2.0: Displays the unique values in the monthly_fee column of bronze_df
print(bronze_df["monthly_fee"].unique())

# Check 2.1 Displays rows where monthly_fee is -100
print((bronze_df["monthly_fee"] == "-100").sum())

# Check 2.3: Count fees containing a currency symbol
print((bronze_df["monthly_fee"].str.contains("R", na=False)).sum())

# Check 2.4: Count thousands separators
print((bronze_df["monthly_fee"].str.contains(",", na=False)).sum())

# Check 2.5: Detect Extra Whitespace
print((
    (bronze_df["monthly_fee"].notna()) &
    (bronze_df["monthly_fee"] != bronze_df["monthly_fee"].str.strip())
).sum())



# ------------end of Column 1: monthly_fee profiling checks------------



# Column 2: signup_date
# Missing values, date formats, invalid dates

# Check 2.6: Displays the unique values in the signup_date column of bronze_df
print(bronze_df["signup_date"].unique())

# Check 2.7: Count invalid date placeholders "not available"
print((bronze_df["signup_date"] == "not available").sum())

# Check 2.8: Date Format Investigation
# Date formats	Three different formats
# Date convention	DD/MM/YYYY assumed

# Column 3: status
# Check 2.9: Displays the number of occurrences of each value
print(bronze_df["status"].value_counts(dropna=False))

# Column 4: plan
# Check 2.10: Displays the number of occurrences of each value
print(bronze_df["plan"].value_counts(dropna=False))

# Column 5: subscription_id
# Check 2.11: Displays the number of occurrences of each value
print(bronze_df[bronze_df["subscription_id"].duplicated(keep=False)])

# Column 6: customer_id
# Check 2.12: Displays the number of occurrences of each value
print(bronze_df["customer_id"].value_counts(dropna=False))


print(" ------End of Level 2 Profiling Checks------")

# STEP 4: PREPARE — Create the Silver working DataFrame
silver_df = bronze_df.copy()

# Confirm that silver_df contains the same number of rows and columns as bronze_df.
print(f"Number of rows in silver_df: {silver_df.shape[0]}")
print(f"Number of columns in silver_df: {silver_df.shape[1]}")

# STEP 5 — TRANSFORM Column-by-column, VALIDATE Column-by-column & LOAD SILVER

print("We'll now clean the data using the issues identified during Bronze profiling.")

# Step 5.1 — Clean monthly_fee

# Step 5.1.1: Remove trailing and leading whitespace from monthly_fee column
silver_df["monthly_fee"] = silver_df["monthly_fee"].str.strip()

# Validate the whitespace transformation
print((
    (silver_df["monthly_fee"].notna()) &
    (silver_df["monthly_fee"] != silver_df["monthly_fee"].str.strip())
).sum())
print("Trailing and leading whitespace removed from monthly_fee column.")

# Step 5.1.2: Remove R currency symbols from monthly_fee column
silver_df["monthly_fee"] = silver_df["monthly_fee"].str.replace("R", "", regex=False)

# Validate the R currency symbol transformation
print(silver_df["monthly_fee"].str.contains("R", na=False).sum())
print("R currency symbols removed from monthly_fee column.")

# Step 5.1.3: Remove Thousands Separators
silver_df["monthly_fee"] = silver_df["monthly_fee"].str.replace(",", "", regex=False)

# Validate the thousands separator transformation
print(silver_df["monthly_fee"].str.contains(",", na=False).sum())
print("Thousands separators removed from monthly_fee column.")

# Step 5.1.4 — Convert monthly_fee to Numeric
silver_df["monthly_fee"] = pd.to_numeric(silver_df["monthly_fee"], errors='coerce')
print(silver_df["monthly_fee"].dtype)
print("monthly_fee column converted to numeric.")

# Step 5.1.5 — Checks: How many missing monthly fees remain in Silver after numeric conversion?"
print(f"missing monthly fees in silver after numeric conversion: {silver_df['monthly_fee'].isnull().sum()}")


# 5.1.6 — Decide How to Handle Missing Monthly Fees

# Now we've reached a business decision, not just a Python coding problem
# Preserve missing fees as NaN and flag the records for investigation.
# We'll introduce a new column called fee_missing.

# Step 5.1.6 — Create the missing-fee flag column in silver_df
silver_df["fee_missing"] = silver_df["monthly_fee"].isnull()

# Step 5.1.7 — Validate the missing-fee flag column
print(f'Displaying value counts for fee_missing column: {silver_df["fee_missing"].value_counts(dropna=False)}')

# Step 5.1.8: Handle Negative Monthly Fees
# Preserve these values and create a separate fee_negative flag.
silver_df["fee_negative"] = silver_df["monthly_fee"] < 0

# Step 5.1.9 — Validate the fee_negative flag column
print(f'Displaying value counts for fee_negative column: {silver_df["fee_negative"].value_counts(dropna=False)}')


print("------End of Step 5.1: Clean monthly_fee column------")


# STEP 5.2 — TRANSFORM SIGNUP_DATE

# Step 5.2.1: Replace invalid placeholders
silver_df["signup_date"] = silver_df["signup_date"].replace("not available", pd.NA)

# Validate missing dates
print(silver_df["signup_date"].isnull().sum())

# Step 5.2.2: Previous conversion — disabled
# silver_df["signup_date"] = pd.to_datetime(
#     silver_df["signup_date"],
#     errors="coerce",
#     format="mixed",
#     dayfirst=True
# )

# Step 5.2.2: Correct date conversion

# Step 5.2.2A: create a temporary column called signup_date_parsed to convert the first date format, YYYY-MM-DD,
silver_df["signup_date_parsed"] = pd.to_datetime(silver_df["signup_date"], format="%Y-%m-%d", errors="coerce")

# Validate the first conversion
print("Validate the first conversion")
print(silver_df["signup_date_parsed"].unique())

# Step 5.2.2B: Parse DD/MM/YYYY Dates
dates_ddmmyyyy = pd.to_datetime(silver_df["signup_date"], format="%d/%m/%Y", errors="coerce")

# Validate DD/MM/YYYY Conversion
print(dates_ddmmyyyy.unique())


# Step 5.2.2C: Parse YYYY/MM/DD Dates
dates_yyyymmdd = pd.to_datetime(silver_df["signup_date"], format="%Y/%m/%d", errors="coerce")

# Validate YYYY/MM/DD Conversion
print(dates_yyyymmdd.unique())

# Step 5.2.2D: Combine Our Parsed Dates
silver_df["signup_date_parsed"] = silver_df["signup_date_parsed"].fillna(dates_ddmmyyyy)

# Combine the Third Date Format
silver_df["signup_date_parsed"] = silver_df["signup_date_parsed"].fillna(dates_yyyymmdd)

# Step 5.2.3: Validate Combined Dates
print(silver_df["signup_date_parsed"].unique())

# Validate the Missing-Date Count
print(silver_df["signup_date_parsed"].isnull().sum())

print("This is an important milestone. We've handled three different date formats without losing any additional date values.")

# Step 5.2.4: Finalize the signup_date Column
silver_df["signup_date"] = silver_df["signup_date_parsed"]

# Step 5.2.5: Remove the Temporary Column
silver_df = silver_df.drop(columns=["signup_date_parsed"])

# Validate the Column Removal
print(silver_df.columns)


# Step 5.2.6: Create a Missing Signup Date Flag
# We previously confirmed that 23 subscription records have missing or invalid signup dates.
# Rather than deleting these records, we want to flag them for investigation.

silver_df["date_missing"] = silver_df["signup_date"].isnull()

# Validate the date_missing Flag
print(silver_df["date_missing"].value_counts(dropna=False))

# Step 5.3 — Standardize status
# Step 5.3.1 — converts strings to lowercase on status cloumn
silver_df["status"] = silver_df["status"].str.lower()

# Step 5.3.2: Validate Status Standardization
print(silver_df["status"].value_counts(dropna=False))

# Step 5.3.3 — Validate Missing and Unexpected Status Values

approved_statuses = ["active", "suspended", "cancelled"]
print(silver_df["status"].isin(approved_statuses).value_counts(dropna=False))

# Step 5.3.4 — Identify Unexpected Status Values
print((silver_df["status"].notna() & ~silver_df["status"].isin(approved_statuses)).sum())

# Step 5.3.5: Create the Missing-Status Flag
silver_df["status_missing"] = silver_df["status"].isnull()

# Step 5.3.6: Validate the Missing-Status Flag
print(silver_df["status_missing"].value_counts(dropna=False))


# Step 5.4. — Standardize Subscription Plans

# Step 5.4.1 -convert all plan names to lowercase
silver_df["plan"] = silver_df["plan"].str.lower()

# Step 5.4.2 - Validate Plan Standardization
print(silver_df["plan"].value_counts(dropna=False))

# Validate Approved Subscription Plans
approved_plans = [
    "cloud pbx",
    "sip trunk",
    "microsoft teams extension",
    "webrtc"
]

print((silver_df["plan"].notna() & ~silver_df["plan"].isin(approved_plans)).sum())


# Step 5.4.4: Validate Missing Subscription Plans
print(silver_df["plan"].isnull().sum())

# Step 5.5: Handle Duplicate Subscriptions
print(silver_df.duplicated().sum())

# 5.5.2 — Remove Exact Duplicates
silver_df = silver_df.drop_duplicates()

# Step 5.5.3: Validate Deduplication
print(silver_df.shape[0])

# Step 5.5.4: Validate Remaining Duplicates
print(silver_df.duplicated().sum())


# Step 5.5.5: Validate Subscription ID Uniqueness
print((silver_df["subscription_id"].duplicated()).sum())

# Step 5.6 — Final Silver Data Quality Validation

# Step 5.6.1 Validate total rows and columns
print(silver_df.shape)

#Step 5.6.2 Validate column data types
print(silver_df.dtypes)

#Step 5.6.3 Validate Missing Values Across All Columns
print(silver_df.isnull().sum())

# Step 5.6.4: Validate Quality Flag Consistency
print((silver_df["fee_missing"] != silver_df["monthly_fee"].isnull()).sum())

# Step 5.6.4.1 Validate fee_negative
print((silver_df["fee_negative"] != (silver_df["monthly_fee"] < 0)).sum())

# Step 5.6.4.2  Validate date_missing
print((silver_df["date_missing"] != silver_df["signup_date"].isnull()).sum())

# Step 5.6.4.3
print((silver_df["status_missing"] != silver_df["status"].isnull()).sum())

# Step 5.6.5: Final Approved-Values Validation
approved_plans = [
    "cloud pbx",
    "sip trunk",
    "microsoft teams extension",
    "webrtc"
]

print((silver_df["plan"].notna() & ~silver_df["plan"].isin(approved_plans)).sum())

print("""
We've completed our planned Silver transformations and validation checks
The unresolved missing and negative values remain flagged for investigation rather than being silently corrected.
      """)


# Step 6: Load Silver into SQLite

silver_df.to_sql(
    name="clean_billing",
    con=conn,
    if_exists="replace",
    index=False
)

# Step 6.2 — Verify Silver Records in SQLite
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM clean_billing")
print(cursor.fetchone())


# Step 6.3: Verify Silver Columns in SQLite
cursor.execute("PRAGMA table_info(clean_billing);")
print(cursor.fetchall())

# Step 6.4 — Verify Bronze Data Integrity
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM raw_billing")
print(cursor.fetchone())