import sqlite3

# ============================================================
# DATABASE PATH
# ============================================================

DB_PATH = "financial_datasets/database/financial_data.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


# ============================================================
# TEST 1: APPLE REVENUE 2024
# ============================================================

print("\n" + "=" * 60)
print("TEST 1: Apple's Revenue in 2024")
print("=" * 60)

cursor.execute("""
SELECT
    c.company_name,
    fc.concept_name,
    p.fiscal_year,
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

WHERE c.company_name = 'Apple Inc.'
  AND fc.concept_name = 'Revenue'
  AND p.fiscal_year = 2024
""")

result = cursor.fetchall()

for row in result:
    print(row)


# ============================================================
# TEST 2: MICROSOFT NET INCOME 2023
# ============================================================

print("\n" + "=" * 60)
print("TEST 2: Microsoft's Net Income in 2023")
print("=" * 60)

cursor.execute("""
SELECT
    c.company_name,
    fc.concept_name,
    p.fiscal_year,
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

WHERE c.company_name = 'Microsoft Corporation'
  AND fc.concept_name = 'Net Income'
  AND p.fiscal_year = 2023
""")

result = cursor.fetchall()

for row in result:
    print(row)


# ============================================================
# TEST 3: AMAZON TOTAL ASSETS 2025
# ============================================================

print("\n" + "=" * 60)
print("TEST 3: Amazon's Total Assets in 2025")
print("=" * 60)

cursor.execute("""
SELECT
    c.company_name,
    fc.concept_name,
    p.fiscal_year,
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

WHERE c.company_name = 'Amazon.com Inc.'
  AND fc.concept_name = 'Total Assets'
  AND p.fiscal_year = 2025
""")

result = cursor.fetchall()

for row in result:
    print(row)


# ============================================================
# TEST 4: SHOW ALL AVAILABLE CONCEPTS
# ============================================================

print("\n" + "=" * 60)
print("TEST 4: Financial Concepts in Database")
print("=" * 60)

cursor.execute("""
SELECT
    concept_name,
    xbrl_tag,
    statement_type
FROM financial_concepts
ORDER BY statement_type, concept_name
""")

for row in cursor.fetchall():
    print(row)


# ============================================================
# CLOSE DATABASE
# ============================================================

conn.close()

print("\n" + "=" * 60)
print("DATABASE TEST COMPLETED")
print("=" * 60)