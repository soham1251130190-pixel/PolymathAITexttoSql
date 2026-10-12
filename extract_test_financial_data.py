import zipfile
import json
import csv
import os


# ============================================================
# SETTINGS
# ============================================================

ZIP_FILE = "financial_datasets/SEC_XBRL/companyfacts.zip"

OUTPUT_DIR = "financial_datasets/SEC_XBRL"
OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "financial_data_test.csv"
)


# Companies for our first test
COMPANIES = {
    "0000320193": "Apple Inc.",
    "0000789019": "Microsoft Corporation",
    "0001018724": "Amazon.com Inc."
}


# ============================================================
# FINANCIAL CONCEPTS
# ============================================================

CONCEPTS = {

    # Income Statement
    "Revenue": (
        "Income Statement",
        "RevenueFromContractWithCustomerExcludingAssessedTax"
    ),

    "Cost of Goods Sold": (
        "Income Statement",
        "CostOfGoodsAndServicesSold"
    ),

    "Gross Profit": (
        "Income Statement",
        "GrossProfit"
    ),

    "Operating Income": (
        "Income Statement",
        "OperatingIncomeLoss"
    ),

    "Net Income": (
        "Income Statement",
        "NetIncomeLoss"
    ),


    # Balance Sheet
    "Total Assets": (
        "Balance Sheet",
        "Assets"
    ),

    "Current Assets": (
        "Balance Sheet",
        "AssetsCurrent"
    ),

    "Total Liabilities": (
        "Balance Sheet",
        "Liabilities"
    ),

    "Current Liabilities": (
        "Balance Sheet",
        "LiabilitiesCurrent"
    ),

    "Stockholders Equity": (
        "Balance Sheet",
        "StockholdersEquity"
    ),

    "Cash and Cash Equivalents": (
        "Balance Sheet",
        "CashAndCashEquivalentsAtCarryingValue"
    ),

    "Inventory": (
        "Balance Sheet",
        "InventoryNet"
    ),

    "Accounts Receivable": (
        "Balance Sheet",
        "AccountsReceivableNetCurrent"
    ),

    "Property Plant and Equipment": (
        "Balance Sheet",
        "PropertyPlantAndEquipmentNet"
    ),


    # Cash Flow Statement
    "Operating Cash Flow": (
        "Cash Flow Statement",
        "NetCashProvidedByUsedInOperatingActivities"
    ),

    "Investing Cash Flow": (
        "Cash Flow Statement",
        "NetCashProvidedByUsedInInvestingActivities"
    ),

    "Financing Cash Flow": (
        "Cash Flow Statement",
        "NetCashProvidedByUsedInFinancingActivities"
    ),

    "Capital Expenditure": (
        "Cash Flow Statement",
        "PaymentsToAcquirePropertyPlantAndEquipment"
    )
}


# ============================================================
# OUTPUT COLUMNS
# ============================================================

FIELDNAMES = [
    "company_name",
    "cik",
    "concept",
    "xbrl_tag",
    "statement_type",
    "value",
    "unit",
    "currency",
    "period_start",
    "period_end",
    "fiscal_year",
    "fiscal_period",
    "form",
    "filing_date",
    "accession_number"
]


# ============================================================
# EXTRACT DATA
# ============================================================

rows = []


with zipfile.ZipFile(ZIP_FILE, "r") as z:

    for cik, company_name in COMPANIES.items():

        filename = f"CIK{cik}.json"

        print("\nProcessing:", company_name)

        try:
            data = json.loads(z.read(filename))

        except KeyError:
            print("File not found:", filename)
            continue

        us_gaap = data.get("facts", {}).get("us-gaap", {})

        for concept_name, (
            statement_type,
            xbrl_tag
        ) in CONCEPTS.items():

            if xbrl_tag not in us_gaap:
                print(
                    "Concept not available:",
                    company_name,
                    xbrl_tag
                )
                continue

            concept_data = us_gaap[xbrl_tag]

            units = concept_data.get("units", {})

            if "USD" not in units:
                print(
                    "USD data not available:",
                    company_name,
                    xbrl_tag
                )
                continue

            observations = units["USD"]

            for obs in observations:

                # We currently want annual 10-K data only
                if obs.get("form") != "10-K":
                    continue

                if obs.get("fp") != "FY":
                    continue

                row = {
                    "company_name": company_name,
                    "cik": cik,
                    "concept": concept_name,
                    "xbrl_tag": xbrl_tag,
                    "statement_type": statement_type,
                    "value": obs.get("val"),
                    "unit": "USD",
                    "currency": "USD",
                    "period_start": obs.get("start"),
                    "period_end": obs.get("end"),
                    "fiscal_year": obs.get("fy"),
                    "fiscal_period": obs.get("fp"),
                    "form": obs.get("form"),
                    "filing_date": obs.get("filed"),
                    "accession_number": obs.get("accn")
                }

                rows.append(row)


# ============================================================
# SAVE CSV
# ============================================================

os.makedirs(OUTPUT_DIR, exist_ok=True)


with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=FIELDNAMES
    )

    writer.writeheader()
    writer.writerows(rows)


print("\n" + "=" * 70)
print("EXTRACTION COMPLETED")
print("=" * 70)

print("Rows extracted:", len(rows))
print("Output file:", OUTPUT_FILE)