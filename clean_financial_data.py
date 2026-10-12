import pandas as pd
import os

INPUT_FILE = "financial_datasets/SEC_XBRL/financial_data_test.csv"

OUTPUT_FILE = "financial_datasets/SEC_XBRL/financial_data_clean.csv"


# ---------------------------------------------------------
# 1. Load extracted data
# ---------------------------------------------------------

df = pd.read_csv(INPUT_FILE)

print("Original rows:", len(df))


# ---------------------------------------------------------
# 2. Convert dates
# ---------------------------------------------------------

df["period_start"] = pd.to_datetime(
    df["period_start"],
    errors="coerce"
)

df["period_end"] = pd.to_datetime(
    df["period_end"],
    errors="coerce"
)

df["filing_date"] = pd.to_datetime(
    df["filing_date"],
    errors="coerce"
)


# ---------------------------------------------------------
# 3. Keep 10-K annual filing data
# ---------------------------------------------------------

df = df[
    (df["form"] == "10-K") &
    (df["fiscal_period"] == "FY")
].copy()

print("After 10-K + FY filter:", len(df))


# ---------------------------------------------------------
# 4. Calculate duration
# ---------------------------------------------------------

df["duration_days"] = (
    df["period_end"] - df["period_start"]
).dt.days


# ---------------------------------------------------------
# 5. Keep:
#
# A. Annual duration facts
#    approximately one year
#
# B. Instantaneous facts
#    used for Balance Sheet values
# ---------------------------------------------------------

annual_duration = (
    df["period_start"].notna() &
    df["period_end"].notna() &
    df["duration_days"].between(330, 400)
)

instantaneous = (
    df["period_start"].isna() &
    df["period_end"].notna()
)

df = df[
    annual_duration | instantaneous
].copy()

print("After annual/instantaneous filter:", len(df))


# ---------------------------------------------------------
# 6. IMPORTANT:
#
# Determine the actual fiscal year from the reporting
# period end date.
#
# This prevents a historical comparative fact appearing
# in a later filing from becoming a new fiscal-year record.
#
# Example:
#
# Apple:
# 2023-10-01 -> 2024-09-28
#
# is FY2024 even if it appears in a FY2025 filing.
#
# ---------------------------------------------------------

# Preserve the original SEC fiscal year

# Create the normalized fiscal year used by our project
df["actual_fiscal_year"] = df["period_end"].dt.year


# ---------------------------------------------------------
# 7. For each actual financial period, keep one record.
#
# The period itself is the identity of the financial fact.
#
# We prefer the filing whose fiscal year matches the actual
# period-end year.
#
# If multiple matching records exist, use the earliest
# filing that reports that period.
# ---------------------------------------------------------

df["fiscal_year_match"] = (
    df["fiscal_year"] == df["actual_fiscal_year"]
)


# Sort so that:
# 1. Correct fiscal-year filing comes first
# 2. Earliest filing comes first

df = df.sort_values(
    [
        "company_name",
        "concept",
        "period_end",
        "fiscal_year_match",
        "filing_date"
    ],
    ascending=[
        True,
        True,
        True,
        False,
        True
    ]
)


# ---------------------------------------------------------
# 8. Remove repeated historical comparative records
#
# For duration facts:
#   company + concept + period_start + period_end
#
# For instantaneous facts:
#   company + concept + period_end
#
# ---------------------------------------------------------

duration_mask = df["period_start"].notna()

duration_rows = df[duration_mask].copy()

instant_rows = df[~duration_mask].copy()


duration_rows = duration_rows.drop_duplicates(
    subset=[
        "company_name",
        "concept",
        "period_start",
        "period_end"
    ],
    keep="first"
)


instant_rows = instant_rows.drop_duplicates(
    subset=[
        "company_name",
        "concept",
        "period_end"
    ],
    keep="first"
)


# Combine both types

df = pd.concat(
    [
        duration_rows,
        instant_rows
    ],
    ignore_index=True
)


# ---------------------------------------------------------
# 9. Set fiscal year to the actual reporting period year
# ---------------------------------------------------------

df["fiscal_year"] = df["actual_fiscal_year"]


# ---------------------------------------------------------
# 10. Remove helper columns
# ---------------------------------------------------------

df = df.drop(
    columns=[
        "actual_fiscal_year",
        "fiscal_year_match",
        "duration_days"
    ]
)


# ---------------------------------------------------------
# 11. Sort final dataset
# ---------------------------------------------------------

df = df.sort_values(
    [
        "company_name",
        "period_end",
        "concept"
    ]
).reset_index(drop=True)


# ---------------------------------------------------------
# 12. Save
# ---------------------------------------------------------

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ---------------------------------------------------------
# 13. Display results
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("FINAL CLEANING COMPLETED")
print("=" * 70)

print("Final rows:", len(df))
print("Columns:", len(df.columns))

print("\nRows per company:")
print(
    df["company_name"].value_counts()
)

print("\nRows per statement type:")
print(
    df["statement_type"].value_counts()
)

print("\nOutput file:")
print(OUTPUT_FILE)