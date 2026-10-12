import sqlite3

DB_PATH = "financial_datasets/database/financial_data.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 60)
print("CHECKING FOR DUPLICATE FINANCIAL FACTS")
print("=" * 60)

cursor.execute("""
SELECT
    c.company_name,
    fc.concept_name,
    p.fiscal_year,
    COUNT(*) AS count
FROM financial_facts ff

JOIN companies c
    ON ff.company_id = c.company_id

JOIN financial_concepts fc
    ON ff.concept_id = fc.concept_id

JOIN periods p
    ON ff.period_id = p.period_id

GROUP BY
    c.company_name,
    fc.concept_name,
    p.fiscal_year

HAVING COUNT(*) > 1

ORDER BY
    c.company_name,
    fc.concept_name,
    p.fiscal_year
""")

duplicates = cursor.fetchall()

if duplicates:
    print("\nDuplicates found:\n")

    for row in duplicates:
        print(row)

else:
    print("\nNo duplicates found.")
    print("Database passed the duplicate check.")


conn.close()

print("\n" + "=" * 60)