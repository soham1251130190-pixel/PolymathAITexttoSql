from pathlib import Path
import pandas as pd


# ============================================================
# PATHS
# ============================================================

DATA_PATH = Path(
    "financial_datasets/SEC_XBRL/financial_data_clean.csv"
)

SCHEMA_PATH = Path(
    "financial_datasets/schema/financial_schema_catalog.csv"
)

OUTPUT_PATH = Path(
    "financial_datasets/schema/financial_metadata.md"
)


# ============================================================
# LOAD DATA
# ============================================================

data = pd.read_csv(DATA_PATH)

schema = pd.read_csv(SCHEMA_PATH)


# ============================================================
# BASIC INFORMATION
# ============================================================

companies = sorted(data["company_name"].unique())

concept_count = data["concept"].nunique()

row_count = len(data)

statement_counts = (
    data["statement_type"]
    .value_counts()
    .to_dict()
)


# ============================================================
# BUILD DOCUMENT
# ============================================================

lines = []

lines.append("# Financial Data Metadata Documentation")
lines.append("")

lines.append("## 1. Purpose")
lines.append("")
lines.append(
    "This document describes the financial data layer used in the "
    "Text-to-SQL over Financial Data project. It explains the source "
    "of the financial data, the selected financial concepts, the "
    "database structure, period handling, filing information, units "
    "and currency, and the data-cleaning approach."
)
lines.append("")


# ============================================================
# DATA SOURCE
# ============================================================

lines.append("## 2. Financial Data Source")
lines.append("")

lines.append(
    "The initial financial dataset is based on SEC XBRL Company Facts "
    "data. SEC Company Facts provides structured financial facts "
    "reported by companies through XBRL filings."
)

lines.append("")

lines.append(
    "The project uses selected US-GAAP financial concepts and "
    "corresponding XBRL tags rather than using every available XBRL "
    "concept."
)

lines.append("")


# ============================================================
# DATASET
# ============================================================

lines.append("## 3. Current Dataset")
lines.append("")

lines.append(f"- Companies: {len(companies)}")
lines.append(f"- Financial concepts: {concept_count}")
lines.append(f"- Clean financial records: {row_count}")

lines.append("")

lines.append("### Companies")

for company in companies:
    lines.append(f"- {company}")

lines.append("")


# ============================================================
# STATEMENT TYPES
# ============================================================

lines.append("## 4. Financial Statement Types")
lines.append("")

for statement, count in statement_counts.items():
    lines.append(f"- {statement}: {count} records")

lines.append("")

lines.append(
    "The selected concepts cover three major financial statement "
    "categories: Income Statement, Balance Sheet, and Cash Flow Statement."
)

lines.append("")


# ============================================================
# CONCEPT CATALOG
# ============================================================

lines.append("## 5. Financial Concept Catalog")
lines.append("")

lines.append(
    "The project maps user-facing financial concepts to selected "
    "SEC XBRL tags. The schema catalog contains descriptions, "
    "statement types, period types, expected units, query types, "
    "and search terms."
)

lines.append("")

lines.append(
    "| Concept | XBRL Tag | Statement Type | Period Type | Query Type |"
)
lines.append("|---|---|---|---|---|")

for _, row in schema.iterrows():

    lines.append(
        f"| {row['concept_name']} "
        f"| `{row['xbrl_tag']}` "
        f"| {row['statement_type']} "
        f"| {row['period_type']} "
        f"| {row['query_type']} |"
    )

lines.append("")


# ============================================================
# PERIOD HANDLING
# ============================================================

lines.append("## 6. Period and Fiscal Year Handling")
lines.append("")

lines.append(
    "Financial facts are stored using their actual reporting period "
    "start and end dates."
)

lines.append("")

lines.append(
    "The fiscal year used in the cleaned dataset is normalized from "
    "the period end date so that the financial period is represented "
    "consistently."
)

lines.append("")

lines.append(
    "Income Statement and Cash Flow Statement concepts are duration "
    "facts because they represent financial activity over a reporting "
    "period."
)

lines.append("")

lines.append(
    "Balance Sheet concepts are instant facts because they represent "
    "financial position at a specific reporting date."
)

lines.append("")


# ============================================================
# DATA CLEANING
# ============================================================

lines.append("## 7. Data Cleaning and Duplicate Handling")
lines.append("")

lines.append(
    "The raw Company Facts data can contain multiple observations "
    "for the same financial period because filings may include "
    "historical comparative figures."
)

lines.append("")

lines.append(
    "The cleaning process therefore:"
)

lines.append(
    "1. Selects annual 10-K fiscal-year facts."
)

lines.append(
    "2. Keeps annual duration facts with an appropriate annual "
    "period length."
)

lines.append(
    "3. Keeps instantaneous facts for Balance Sheet concepts."
)

lines.append(
    "4. Uses the actual period dates to identify the financial year."
)

lines.append(
    "5. Removes duplicate observations for the same company, "
    "concept, and financial period."
)

lines.append(
    "6. Prefers the filing whose reported fiscal year matches "
    "the actual fiscal year represented by the period."
)

lines.append("")


# ============================================================
# UNITS AND CURRENCY
# ============================================================

lines.append("## 8. Units and Currency")
lines.append("")

lines.append(
    "Each financial fact stores its unit and currency information."
)

lines.append("")

lines.append(
    "The current SEC dataset contains financial values represented "
    "in USD, with the unit and currency stored explicitly in the "
    "database."
)

lines.append("")


# ============================================================
# DATABASE STRUCTURE
# ============================================================

lines.append("## 9. Database Structure")
lines.append("")

lines.append(
    "The cleaned financial data is stored in an SQLite database."
)

lines.append("")

lines.append("### Companies")

lines.append(
    "Stores company identity information such as company name and CIK."
)

lines.append("")

lines.append("### Financial Concepts")

lines.append(
    "Stores the financial concept name, SEC XBRL tag, and statement type."
)

lines.append("")

lines.append("### Periods")

lines.append(
    "Stores period start date, period end date, fiscal year, "
    "and fiscal period."
)

lines.append("")

lines.append("### Filings")

lines.append(
    "Stores filing-level information such as accession number, "
    "filing date, and form."
)

lines.append("")

lines.append("### Financial Facts")

lines.append(
    "Stores the actual financial value and connects the value to "
    "a company, financial concept, reporting period, and filing."
)

lines.append("")


# ============================================================
# DATABASE RELATIONSHIP
# ============================================================

lines.append("## 10. Financial Fact Relationship")
lines.append("")

lines.append(
    "A financial fact connects the following information:"
)

lines.append("")

lines.append(
    "Company + Financial Concept + Period + Filing + Value + Unit + Currency"
)

lines.append("")

lines.append(
    "This structure allows the system to retrieve a financial value "
    "while preserving its company, concept, reporting period, and "
    "filing context."
)

lines.append("")


# ============================================================
# SCHEMA SEARCH
# ============================================================

lines.append("## 11. Financial Schema Search Support")
lines.append("")

lines.append(
    "The schema catalog contains alternative search terms for "
    "financial concepts. Entity mappings also connect common "
    "user terminology to the canonical database concepts."
)

lines.append("")

lines.append("Examples:")

lines.append("- sales → Revenue")
lines.append("- profit → Net Income")
lines.append("- assets → Total Assets")
lines.append("- capex → Capital Expenditure")
lines.append("- cash from operations → Operating Cash Flow")

lines.append("")


# ============================================================
# CURRENT VALIDATION
# ============================================================

lines.append("## 12. Current Validation")
lines.append("")

lines.append(
    "The current database has been tested using financial queries "
    "for Apple, Microsoft, and Amazon."
)

lines.append("")

lines.append(
    "The database verification also confirmed that no duplicate "
    "records were found for company, financial concept, and fiscal year "
    "within the cleaned dataset."
)

lines.append("")


# ============================================================
# FILES
# ============================================================

lines.append("## 13. Member 1 Data Layer Files")
lines.append("")

lines.append(
    "- `financial_data_clean.csv` — cleaned SEC financial data"
)

lines.append(
    "- `financial_data.db` — SQLite financial database"
)

lines.append(
    "- `financial_schema_catalog.csv` — financial concept metadata"
)

lines.append(
    "- `entity_mappings.csv` — common user terms mapped to "
    "canonical financial concepts and companies"
)

lines.append("")


# ============================================================
# WRITE FILE
# ============================================================

OUTPUT_PATH.write_text(
    "\n".join(lines),
    encoding="utf-8"
)


print("=" * 60)
print("FINANCIAL METADATA DOCUMENTATION CREATED")
print("=" * 60)

print(f"\nOutput file:")
print(OUTPUT_PATH)

print(f"\nCompanies documented: {len(companies)}")
print(f"Financial concepts documented: {concept_count}")
print(f"Financial records documented: {row_count}")

print("\n" + "=" * 60)
print("DOCUMENTATION COMPLETE")
print("=" * 60)