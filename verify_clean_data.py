import pandas as pd

FILE = "financial_datasets/SEC_XBRL/financial_data_clean.csv"

df = pd.read_csv(FILE)

print("=" * 70)
print("CLEAN DATA VERIFICATION")
print("=" * 70)

# ---------------------------------------------------------
# 1. Basic information
# ---------------------------------------------------------

print("\nTotal rows:", len(df))
print("Total companies:", df["company_name"].nunique())
print("Total concepts:", df["concept"].nunique())

# ---------------------------------------------------------
# 2. Show available concepts
# ---------------------------------------------------------

print("\nFinancial concepts:")
for concept in sorted(df["concept"].unique()):
    print(" -", concept)

# ---------------------------------------------------------
# 3. Check Apple revenue
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("APPLE REVENUE")
print("=" * 70)

apple_revenue = df[
    (df["company_name"] == "Apple Inc.") &
    (df["concept"] == "Revenue")
].copy()

print(
    apple_revenue[
        [
            "value",
            "period_start",
            "period_end",
            "fiscal_year",
            "filing_date"
        ]
    ].tail(10).to_string(index=False)
)

# ---------------------------------------------------------
# 4. Check Microsoft revenue
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("MICROSOFT REVENUE")
print("=" * 70)

microsoft_revenue = df[
    (df["company_name"] == "Microsoft Corporation") &
    (df["concept"] == "Revenue")
].copy()

print(
    microsoft_revenue[
        [
            "value",
            "period_start",
            "period_end",
            "fiscal_year",
            "filing_date"
        ]
    ].tail(10).to_string(index=False)
)

# ---------------------------------------------------------
# 5. Check Amazon revenue
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("AMAZON REVENUE")
print("=" * 70)

amazon_revenue = df[
    (df["company_name"] == "Amazon.com Inc.") &
    (df["concept"] == "Revenue")
].copy()

print(
    amazon_revenue[
        [
            "value",
            "period_start",
            "period_end",
            "fiscal_year",
            "filing_date"
        ]
    ].tail(10).to_string(index=False)
)

# ---------------------------------------------------------
# 6. Check latest period for each company
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("LATEST PERIOD BY COMPANY")
print("=" * 70)

print(
    df.groupby("company_name")["period_end"]
      .max()
)

# ---------------------------------------------------------
# 7. Check missing values
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("MISSING VALUES")
print("=" * 70)

print(df.isna().sum())

print("\nVerification completed.")