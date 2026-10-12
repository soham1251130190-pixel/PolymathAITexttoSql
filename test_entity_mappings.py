import pandas as pd
from pathlib import Path


# ============================================================
# PATH
# ============================================================

MAPPING_PATH = Path(
    "financial_datasets/schema/entity_mappings.csv"
)


# ============================================================
# LOAD MAPPINGS
# ============================================================

df = pd.read_csv(MAPPING_PATH)


# ============================================================
# FUNCTION: MAP USER TERM
# ============================================================

def map_term(user_term, entity_type):

    user_term = user_term.strip().lower()

    result = df[
        (df["user_term"] == user_term) &
        (df["entity_type"] == entity_type)
    ]

    if result.empty:
        return None

    return result.iloc[0]["database_value"]


# ============================================================
# TEST CASES
# ============================================================

tests = [
    ("apple", "company"),
    ("microsoft", "company"),
    ("amazon", "company"),

    ("sales", "financial_concept"),
    ("profit", "financial_concept"),
    ("assets", "financial_concept"),
    ("capex", "financial_concept"),
    ("cash from operations", "financial_concept"),
]


print("=" * 60)
print("ENTITY MAPPING TEST")
print("=" * 60)


for user_term, entity_type in tests:

    mapped_value = map_term(
        user_term,
        entity_type
    )

    print(
        f"\nUser term      : {user_term}"
        f"\nEntity type    : {entity_type}"
        f"\nMapped value   : {mapped_value}"
    )


print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)