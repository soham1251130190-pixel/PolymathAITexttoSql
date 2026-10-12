import zipfile
import json

ZIP_FILE = "financial_datasets/SEC_XBRL/companyfacts.zip"
COMPANY_FILE = "CIK0000320193.json"

with zipfile.ZipFile(ZIP_FILE, "r") as z:

    data = json.loads(z.read(COMPANY_FILE))

us_gaap = data["facts"]["us-gaap"]

print("=" * 80)
print("APPLE INC. - MAJOR FINANCIAL CONCEPTS")
print("=" * 80)

# Important concepts for our financial database
CONCEPT_GROUPS = {

    "INCOME STATEMENT": [
        "Revenue",
        "SalesRevenue",
        "Revenues",
        "RevenueFromContractWithCustomer",
        "CostOfGoods",
        "GrossProfit",
        "OperatingIncome",
        "NetIncome"
    ],

    "BALANCE SHEET": [
        "Assets",
        "Liabilities",
        "StockholdersEquity",
        "CashAndCashEquivalents",
        "AccountsReceivable",
        "Inventory",
        "PropertyPlantAndEquipment"
    ],

    "CASH FLOW STATEMENT": [
        "NetCashProvided",
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInInvestingActivities",
        "NetCashProvidedByUsedInFinancingActivities",
        "PaymentsToAcquirePropertyPlantAndEquipment"
    ]
}


for group_name, keywords in CONCEPT_GROUPS.items():

    print("\n" + "=" * 80)
    print(group_name)
    print("=" * 80)

    found = set()

    for tag, details in us_gaap.items():

        label = details.get("label") or ""
        description = details.get("description") or ""

        searchable_text = (
            tag + " " +
            label + " " +
            description
        ).lower()

        for keyword in keywords:

            if keyword.lower() in searchable_text:

                if tag not in found:

                    found.add(tag)

                    units = list(
                        details.get("units", {}).keys()
                    )

                    print("\nTAG:", tag)
                    print("LABEL:", label)
                    print("UNITS:", units)

                break


print("\n" + "=" * 80)
print("Inspection completed.")
print("=" * 80)