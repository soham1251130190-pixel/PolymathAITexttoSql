import sqlite3
import pandas as pd
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

DB_PATH = Path(
    "financial_datasets/database/financial_data.db"
)

MAPPING_PATH = Path(
    "financial_datasets/schema/entity_mappings.csv"
)


# ============================================================
# LOAD ENTITY MAPPINGS
# ============================================================

mappings = pd.read_csv(MAPPING_PATH)


# ============================================================
# CONNECT TO DATABASE
# ============================================================

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row


# ============================================================
# FUNCTION: MAP USER TERM
# ============================================================

def map_term(user_term, entity_type):

    user_term = user_term.strip().lower()

    result = mappings[
        (mappings["user_term"] == user_term) &
        (mappings["entity_type"] == entity_type)
    ]

    if result.empty:
        return None

    return result.iloc[0]["database_value"]


# ============================================================
# FUNCTION: QUERY DATABASE
# ============================================================

def get_financial_value(
    company_name,
    concept_name,
    fiscal_year
):

    query = """
    SELECT
        c.company_name,
        fc.concept_name,
        fc.statement_type,
        p.fiscal_year,
        p.period_start,
        p.period_end,
        ff.value,
        ff.unit,
        ff.currency
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
        (
            company_name,
            concept_name,
            fiscal_year
        )
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
# MAIN PIPELINE
# ============================================================

print("=" * 60)
print("FINANCIAL QUERY PIPELINE")
print("=" * 60)


# ------------------------------------------------------------
# USER INPUT
# ------------------------------------------------------------

user_company = input(
    "\nEnter company: "
).strip()

user_concept = input(
    "Enter financial term: "
).strip()

user_year = input(
    "Enter fiscal year: "
).strip()


# ------------------------------------------------------------
# CONVERT YEAR
# ------------------------------------------------------------

try:

    fiscal_year = int(user_year)

except ValueError:

    print(
        "\nInvalid fiscal year. "
        "Please enter a number such as 2024."
    )

    conn.close()
    exit()


# ------------------------------------------------------------
# MAP COMPANY
# ------------------------------------------------------------

company_name = map_term(
    user_company,
    "company"
)


if company_name is None:

    print(
        f"\nCould not identify company: "
        f"{user_company}"
    )

    print(
        "\nPlease use a supported company "
        "or add a new company mapping."
    )

    conn.close()
    exit()


# ------------------------------------------------------------
# MAP FINANCIAL CONCEPT
# ------------------------------------------------------------

concept_name = map_term(
    user_concept,
    "financial_concept"
)


if concept_name is None:

    print(
        f"\nCould not identify financial concept: "
        f"{user_concept}"
    )

    print(
        "\nPlease use a supported financial term "
        "or add a new concept mapping."
    )

    conn.close()
    exit()


# ------------------------------------------------------------
# SHOW INTERPRETATION
# ------------------------------------------------------------

print("\n" + "-" * 60)
print("QUERY INTERPRETATION")
print("-" * 60)

print(f"User company term : {user_company}")
print(f"Mapped company    : {company_name}")

print(f"\nUser financial term : {user_concept}")
print(f"Mapped concept     : {concept_name}")

print(f"\nFiscal year        : {fiscal_year}")


# ------------------------------------------------------------
# QUERY DATABASE
# ------------------------------------------------------------

result = get_financial_value(
    company_name,
    concept_name,
    fiscal_year
)


# ------------------------------------------------------------
# DISPLAY RESULT
# ------------------------------------------------------------

display_result(result)


# ============================================================
# CLOSE DATABASE
# ============================================================

conn.close()