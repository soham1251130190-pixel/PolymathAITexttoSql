import pandas as pd
from pathlib import Path


# ============================================================
# PATH
# ============================================================

SCHEMA_PATH = Path(
    "financial_datasets/schema/financial_schema_catalog.csv"
)

OUTPUT_PATH = Path(
    "financial_datasets/schema/entity_mappings.csv"
)


# ============================================================
# LOAD SCHEMA CATALOG
# ============================================================

schema = pd.read_csv(SCHEMA_PATH)


# ============================================================
# COMPANY MAPPINGS
# ============================================================

company_mappings = [

    {
        "entity_type": "company",
        "user_term": "apple",
        "database_value": "Apple Inc."
    },

    {
        "entity_type": "company",
        "user_term": "apple inc",
        "database_value": "Apple Inc."
    },

    {
        "entity_type": "company",
        "user_term": "apple inc.",
        "database_value": "Apple Inc."
    },

    {
        "entity_type": "company",
        "user_term": "microsoft",
        "database_value": "Microsoft Corporation"
    },

    {
        "entity_type": "company",
        "user_term": "microsoft corporation",
        "database_value": "Microsoft Corporation"
    },

    {
        "entity_type": "company",
        "user_term": "amazon",
        "database_value": "Amazon.com Inc."
    },

    {
        "entity_type": "company",
        "user_term": "amazon.com",
        "database_value": "Amazon.com Inc."
    },

    {
        "entity_type": "company",
        "user_term": "amazon.com inc",
        "database_value": "Amazon.com Inc."
    }
]


# ============================================================
# CONCEPT MAPPINGS
# ============================================================

concept_mappings = []


for _, row in schema.iterrows():

    concept = row["concept_name"]

    # Main concept name
    concept_mappings.append({
        "entity_type": "financial_concept",
        "user_term": concept.lower(),
        "database_value": concept
    })

    # Search terms from schema catalog
    terms = str(row["search_terms"]).split()

    # We will separately define multi-word aliases below.


# ============================================================
# COMMON FINANCIAL ALIASES
# ============================================================

aliases = {

    "Revenue": [
        "sales",
        "sales revenue",
        "total revenue",
        "revenues",
        "income from sales"
    ],

    "Cost of Goods Sold": [
        "cogs",
        "cost of sales",
        "cost of goods",
        "cost of goods and services sold"
    ],

    "Gross Profit": [
        "gross profit"
    ],

    "Operating Income": [
        "operating profit",
        "operating earnings"
    ],

    "Net Income": [
        "net profit",
        "net earnings",
        "profit",
        "earnings",
        "bottom line"
    ],

    "Total Assets": [
        "assets",
        "total assets"
    ],

    "Current Assets": [
        "current assets"
    ],

    "Total Liabilities": [
        "liabilities",
        "total liabilities"
    ],

    "Current Liabilities": [
        "current liabilities"
    ],

    "Stockholders Equity": [
        "shareholders equity",
        "shareholder equity",
        "stockholders equity",
        "equity"
    ],

    "Cash and Cash Equivalents": [
        "cash",
        "cash equivalents",
        "cash and equivalents"
    ],

    "Inventory": [
        "inventory",
        "stock"
    ],

    "Accounts Receivable": [
        "receivables",
        "accounts receivable",
        "trade receivables"
    ],

    "Property Plant and Equipment": [
        "ppe",
        "pp&e",
        "property plant equipment",
        "fixed assets"
    ],

    "Operating Cash Flow": [
        "cash from operations",
        "operating cash",
        "cash flow from operations"
    ],

    "Investing Cash Flow": [
        "cash from investing",
        "investing cash",
        "cash flow from investing"
    ],

    "Financing Cash Flow": [
        "cash from financing",
        "financing cash",
        "cash flow from financing"
    ],

    "Capital Expenditure": [
        "capex",
        "capital spending",
        "capital expenditures",
        "capital expenditure"
    ]
}


# ============================================================
# ADD ALIASES
# ============================================================

for concept, terms in aliases.items():

    for term in terms:

        concept_mappings.append({
            "entity_type": "financial_concept",
            "user_term": term.lower(),
            "database_value": concept
        })


# ============================================================
# COMBINE MAPPINGS
# ============================================================

all_mappings = (
    company_mappings +
    concept_mappings
)


df = pd.DataFrame(all_mappings)


# ============================================================
# REMOVE DUPLICATES
# ============================================================

df = df.drop_duplicates(
    subset=[
        "entity_type",
        "user_term",
        "database_value"
    ]
)


# ============================================================
# SORT
# ============================================================

df = df.sort_values(
    by=[
        "entity_type",
        "user_term"
    ]
)


# ============================================================
# SAVE
# ============================================================

df.to_csv(
    OUTPUT_PATH,
    index=False
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("=" * 60)
print("ENTITY MAPPING CREATED")
print("=" * 60)

print(f"\nTotal mappings: {len(df)}")

print("\nMappings by entity type:")
print(
    df["entity_type"].value_counts()
)

print("\nOutput file:")
print(OUTPUT_PATH)

print("\nSample mappings:")
print(
    df.head(20).to_string(index=False)
)

print("\n" + "=" * 60)
print("ENTITY MAPPING COMPLETE")
print("=" * 60)