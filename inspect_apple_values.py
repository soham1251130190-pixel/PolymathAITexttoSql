import zipfile
import json

ZIP_FILE = "financial_datasets/SEC_XBRL/companyfacts.zip"
COMPANY_FILE = "CIK0000320193.json"

# Core concepts we selected
CONCEPTS = {
    "Revenue": "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Cost of Goods Sold": "CostOfGoodsAndServicesSold",
    "Gross Profit": "GrossProfit",
    "Operating Income": "OperatingIncomeLoss",
    "Net Income": "NetIncomeLoss",

    "Total Assets": "Assets",
    "Current Assets": "AssetsCurrent",
    "Total Liabilities": "Liabilities",
    "Current Liabilities": "LiabilitiesCurrent",
    "Stockholders Equity": "StockholdersEquity",
    "Cash and Cash Equivalents": "CashAndCashEquivalentsAtCarryingValue",
    "Inventory": "InventoryNet",
    "Accounts Receivable": "AccountsReceivableNetCurrent",
    "Property Plant and Equipment": "PropertyPlantAndEquipmentNet",

    "Operating Cash Flow": "NetCashProvidedByUsedInOperatingActivities",
    "Investing Cash Flow": "NetCashProvidedByUsedInInvestingActivities",
    "Financing Cash Flow": "NetCashProvidedByUsedInFinancingActivities",
    "Capital Expenditure": "PaymentsToAcquirePropertyPlantAndEquipment"
}


with zipfile.ZipFile(ZIP_FILE, "r") as z:

    data = json.loads(z.read(COMPANY_FILE))


print("=" * 100)
print("APPLE INC. - ACTUAL FINANCIAL VALUES")
print("=" * 100)

print("Company:", data["entityName"])
print("CIK:", data["cik"])


us_gaap = data["facts"]["us-gaap"]


for concept_name, tag in CONCEPTS.items():

    print("\n")
    print("=" * 100)
    print(concept_name)
    print("SEC TAG:", tag)
    print("=" * 100)

    if tag not in us_gaap:
        print("TAG NOT FOUND")
        continue

    details = us_gaap[tag]

    print("Label:", details.get("label"))
    print("Available units:", list(details.get("units", {}).keys()))

    units = details.get("units", {})

    # Usually USD for these concepts
    if "USD" not in units:
        print("USD observations not available")
        continue

    observations = units["USD"]

    # Show annual 10-K observations
    annual = []

    for obs in observations:

        if obs.get("form") == "10-K" and obs.get("fp") == "FY":
            annual.append(obs)

    # Sort newest filing first
    annual.sort(
        key=lambda x: x.get("filed", ""),
        reverse=True
    )

    print("\nAnnual 10-K observations:")

    for obs in annual[:10]:

        print(
            f"FY={obs.get('fy')} | "
            f"start={obs.get('start')} | "
            f"end={obs.get('end')} | "
            f"value={obs.get('val')} | "
            f"filed={obs.get('filed')} | "
            f"form={obs.get('form')} | "
            f"accn={obs.get('accn')}"
        )


print("\n")
print("=" * 100)
print("INSPECTION COMPLETED")
print("=" * 100)