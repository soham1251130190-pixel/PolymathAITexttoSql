import sqlite3
import pandas as pd
from pathlib import Path

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path("financial_datasets")

CSV_PATH = BASE_DIR / "SEC_XBRL" / "financial_data_clean.csv"
DB_PATH = BASE_DIR / "database" / "financial_data.db"

# Create database folder if it does not exist
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOAD CLEAN DATA
# ============================================================

print("Loading cleaned financial data...")

df = pd.read_csv(CSV_PATH)

print(f"Rows loaded: {len(df)}")
print(f"Columns: {len(df.columns)}")


# ============================================================
# CONNECT TO SQLITE DATABASE
# ============================================================

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("\nConnected to database.")


# ============================================================
# REMOVE OLD TABLES
# ============================================================

cursor.execute("DROP TABLE IF EXISTS financial_facts")
cursor.execute("DROP TABLE IF EXISTS filings")
cursor.execute("DROP TABLE IF EXISTS periods")
cursor.execute("DROP TABLE IF EXISTS financial_concepts")
cursor.execute("DROP TABLE IF EXISTS companies")

conn.commit()


# ============================================================
# 1. COMPANIES TABLE
# ============================================================

cursor.execute("""
CREATE TABLE companies (
    company_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL UNIQUE,
    cik TEXT NOT NULL UNIQUE
)
""")


# ============================================================
# 2. FINANCIAL CONCEPTS TABLE
# ============================================================

cursor.execute("""
CREATE TABLE financial_concepts (
    concept_id INTEGER PRIMARY KEY AUTOINCREMENT,
    concept_name TEXT NOT NULL,
    xbrl_tag TEXT NOT NULL,
    statement_type TEXT NOT NULL,
    UNIQUE(concept_name, xbrl_tag)
)
""")


# ============================================================
# 3. PERIODS TABLE
# ============================================================

cursor.execute("""
CREATE TABLE periods (
    period_id INTEGER PRIMARY KEY AUTOINCREMENT,
    period_start TEXT,
    period_end TEXT NOT NULL,
    fiscal_year INTEGER NOT NULL,
    fiscal_period TEXT NOT NULL,
    UNIQUE(period_start, period_end, fiscal_year, fiscal_period)
)
""")


# ============================================================
# 4. FILINGS TABLE
# ============================================================

cursor.execute("""
CREATE TABLE filings (
    filing_id INTEGER PRIMARY KEY AUTOINCREMENT,
    accession_number TEXT NOT NULL UNIQUE,
    filing_date TEXT NOT NULL,
    form TEXT NOT NULL
)
""")


# ============================================================
# 5. FINANCIAL FACTS TABLE
# ============================================================

cursor.execute("""
CREATE TABLE financial_facts (
    fact_id INTEGER PRIMARY KEY AUTOINCREMENT,

    company_id INTEGER NOT NULL,
    concept_id INTEGER NOT NULL,
    period_id INTEGER NOT NULL,
    filing_id INTEGER NOT NULL,

    value REAL NOT NULL,
    unit TEXT,
    currency TEXT,

    FOREIGN KEY (company_id)
        REFERENCES companies(company_id),

    FOREIGN KEY (concept_id)
        REFERENCES financial_concepts(concept_id),

    FOREIGN KEY (period_id)
        REFERENCES periods(period_id),

    FOREIGN KEY (filing_id)
        REFERENCES filings(filing_id)
)
""")


# ============================================================
# INSERT COMPANIES
# ============================================================

companies = df[
    [
        "company_name",
        "cik"
    ]
].drop_duplicates()

for _, row in companies.iterrows():

    cursor.execute("""
        INSERT INTO companies
        (
            company_name,
            cik
        )
        VALUES (?, ?)
    """, (
        row["company_name"],
        str(row["cik"]).zfill(10)
    ))


# ============================================================
# INSERT FINANCIAL CONCEPTS
# ============================================================

concepts = df[
    [
        "concept",
        "xbrl_tag",
        "statement_type"
    ]
].drop_duplicates()

for _, row in concepts.iterrows():

    cursor.execute("""
        INSERT INTO financial_concepts
        (
            concept_name,
            xbrl_tag,
            statement_type
        )
        VALUES (?, ?, ?)
    """, (
        row["concept"],
        row["xbrl_tag"],
        row["statement_type"]
    ))


# ============================================================
# INSERT PERIODS
# ============================================================

periods = df[
    [
        "period_start",
        "period_end",
        "fiscal_year",
        "fiscal_period"
    ]
].copy()

# Convert missing period_start values to None
# This is needed for instantaneous Balance Sheet facts.
periods["period_start"] = periods["period_start"].where(
    periods["period_start"].notna(),
    None
)

periods = periods.drop_duplicates()

for _, row in periods.iterrows():

    cursor.execute("""
        INSERT INTO periods
        (
            period_start,
            period_end,
            fiscal_year,
            fiscal_period
        )
        VALUES (?, ?, ?, ?)
    """, (
        row["period_start"],
        row["period_end"],
        int(row["fiscal_year"]),
        row["fiscal_period"]
    ))


# ============================================================
# INSERT FILINGS
# ============================================================

filings = df[
    [
        "accession_number",
        "filing_date",
        "form"
    ]
].drop_duplicates()

for _, row in filings.iterrows():

    cursor.execute("""
        INSERT INTO filings
        (
            accession_number,
            filing_date,
            form
        )
        VALUES (?, ?, ?)
    """, (
        row["accession_number"],
        row["filing_date"],
        row["form"]
    ))


conn.commit()


# ============================================================
# CREATE LOOKUP DICTIONARIES
# ============================================================

# ------------------------------------------------------------
# Company lookup
# ------------------------------------------------------------

company_lookup = {}

for row in cursor.execute("""
    SELECT
        company_id,
        company_name
    FROM companies
"""):

    company_lookup[row[1]] = row[0]


# ------------------------------------------------------------
# Financial concept lookup
# ------------------------------------------------------------

concept_lookup = {}

for row in cursor.execute("""
    SELECT
        concept_id,
        concept_name,
        xbrl_tag
    FROM financial_concepts
"""):

    concept_lookup[
        (
            row[1],
            row[2]
        )
    ] = row[0]


# ------------------------------------------------------------
# Period lookup
# ------------------------------------------------------------

period_lookup = {}

for row in cursor.execute("""
    SELECT
        period_id,
        period_start,
        period_end,
        fiscal_year,
        fiscal_period
    FROM periods
"""):

    period_start = row[1]

    # SQLite returns NULL for missing period_start.
    # Keep it as None for consistent dictionary lookup.
    if pd.isna(period_start):
        period_start = None

    period_lookup[
        (
            period_start,
            row[2],
            row[3],
            row[4]
        )
    ] = row[0]


# ------------------------------------------------------------
# Filing lookup
# ------------------------------------------------------------

filing_lookup = {}

for row in cursor.execute("""
    SELECT
        filing_id,
        accession_number
    FROM filings
"""):

    filing_lookup[row[1]] = row[0]


# ============================================================
# INSERT FINANCIAL FACTS
# ============================================================

print("\nInserting financial facts...")

for _, row in df.iterrows():

    # --------------------------------------------------------
    # Find company
    # --------------------------------------------------------

    company_id = company_lookup[
        row["company_name"]
    ]


    # --------------------------------------------------------
    # Find financial concept
    # --------------------------------------------------------

    concept_id = concept_lookup[
        (
            row["concept"],
            row["xbrl_tag"]
        )
    ]


    # --------------------------------------------------------
    # Find period
    # --------------------------------------------------------

    period_start = row["period_start"]

    # Convert pandas NaN to None
    # for instantaneous Balance Sheet facts.
    if pd.isna(period_start):
        period_start = None

    period_id = period_lookup[
        (
            period_start,
            row["period_end"],
            int(row["fiscal_year"]),
            row["fiscal_period"]
        )
    ]


    # --------------------------------------------------------
    # Find filing
    # --------------------------------------------------------

    filing_id = filing_lookup[
        row["accession_number"]
    ]


    # --------------------------------------------------------
    # Insert financial fact
    # --------------------------------------------------------

    cursor.execute("""
        INSERT INTO financial_facts
        (
            company_id,
            concept_id,
            period_id,
            filing_id,
            value,
            unit,
            currency
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        company_id,
        concept_id,
        period_id,
        filing_id,
        float(row["value"]),
        row["unit"],
        row["currency"]
    ))


conn.commit()


# ============================================================
# VERIFY DATABASE
# ============================================================

print("\n" + "=" * 60)
print("DATABASE CREATION COMPLETED")
print("=" * 60)

tables = [
    "companies",
    "financial_concepts",
    "periods",
    "filings",
    "financial_facts"
]

for table in tables:

    cursor.execute(
        f"SELECT COUNT(*) FROM {table}"
    )

    count = cursor.fetchone()[0]

    print(f"{table}: {count} rows")


# ============================================================
# CLOSE DATABASE
# ============================================================

conn.close()

print("\nDatabase saved at:")
print(DB_PATH)