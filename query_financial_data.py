import sqlite3
from pathlib import Path


# ============================================================
# DATABASE PATH
# ============================================================

DB_PATH = Path(
    "financial_datasets/database/financial_data.db"
)


# ============================================================
# CONNECT TO DATABASE
# ============================================================

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row


# ============================================================
# FUNCTION: GET FINANCIAL VALUE
# ============================================================

def get_financial_value(company_name, concept_name, fiscal_year):

    query = """
    SELECT
        c.company_name,
        fc.concept_name,
        p.fiscal_year,
        p.period_start,
        p.period_end,
        ff.value,
        ff.unit,
        ff.currency,
        fc.statement_type
    FROM financial_facts ff

    JOIN companies c
        ON ff.company_id = c.company_id

    JOIN financial_concepts fc
        ON ff.concept_id = fc.concept_id

    JOIN periods p
        ON ff.period_id = p.period_id

    WHERE c.company_name = ?
      AND fc.concept_name = ?
      AND p.fiscal_year = ?

    ORDER BY p.period_end DESC

    LIMIT 1
    """

    result = conn.execute(
        query,
        (company_name, concept_name, fiscal_year)
    ).fetchone()

    return result


# ============================================================
# FUNCTION: DISPLAY RESULT
# ============================================================

def display_result(result):

    if result is None:
        print("\nNo matching financial data found.")
        return

    print("\n" + "=" * 60)
    print("FINANCIAL QUERY RESULT")
    print("=" * 60)

    print(f"Company       : {result['company_name']}")
    print(f"Concept       : {result['concept_name']}")
    print(f"Statement     : {result['statement_type']}")
    print(f"Fiscal Year   : {result['fiscal_year']}")
    print(f"Period Start  : {result['period_start']}")
    print(f"Period End    : {result['period_end']}")
    print(f"Value         : {result['value']}")
    print(f"Unit          : {result['unit']}")
    print(f"Currency      : {result['currency']}")

    print("=" * 60)


# ============================================================
# GET USER INPUT
# ============================================================

print("=" * 60)
print("FINANCIAL DATA QUERY")
print("=" * 60)

print("\nAvailable companies:")
print("1. Apple Inc.")
print("2. Microsoft Corporation")
print("3. Amazon.com Inc.")

company_name = input(
    "\nEnter company name exactly as shown above: "
).strip()


print("\nExamples of financial concepts:")
print("Revenue")
print("Net Income")
print("Total Assets")
print("Gross Profit")
print("Operating Income")
print("Cash and Cash Equivalents")
print("Operating Cash Flow")

concept_name = input(
    "\nEnter financial concept: "
).strip()


fiscal_year = input(
    "\nEnter fiscal year: "
).strip()

# Convert year to integer
try:
    fiscal_year = int(fiscal_year)

except ValueError:
    print("\nInvalid fiscal year. Please enter a number such as 2024.")
    conn.close()
    exit()


# ============================================================
# EXECUTE QUERY
# ============================================================

result = get_financial_value(
    company_name,
    concept_name,
    fiscal_year
)


# ============================================================
# DISPLAY RESULT
# ============================================================

display_result(result)


# ============================================================
# CLOSE DATABASE
# ============================================================

conn.close()