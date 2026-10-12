import pandas as pd
from pathlib import Path

CATALOG_PATH = Path(
    "financial_datasets/schema/financial_schema_catalog.csv"
)

df = pd.read_csv(CATALOG_PATH)

print("=" * 70)
print("SCHEMA CATALOG VERIFICATION")
print("=" * 70)

print(f"\nTotal concepts: {len(df)}")

print("\nColumns:")
for column in df.columns:
    print("-", column)

print("\n" + "=" * 70)
print("FINANCIAL CONCEPTS")
print("=" * 70)

for _, row in df.iterrows():
    print(
        f"\nConcept: {row['concept_name']}"
        f"\nXBRL Tag: {row['xbrl_tag']}"
        f"\nStatement: {row['statement_type']}"
        f"\nPeriod Type: {row['period_type']}"
        f"\nQuery Type: {row['query_type']}"
        f"\nSearch Terms: {row['search_terms']}"
    )

print("\n" + "=" * 70)
print("STATEMENT TYPE COUNTS")
print("=" * 70)

print(df["statement_type"].value_counts())

print("\n" + "=" * 70)
print("PERIOD TYPE COUNTS")
print("=" * 70)

print(df["period_type"].value_counts())

print("\n" + "=" * 70)
print("VERIFICATION COMPLETE")
print("=" * 70)