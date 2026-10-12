import zipfile
import json

ZIP_FILE = "financial_datasets/SEC_XBRL/companyfacts.zip"
COMPANY_FILE = "CIK0000320193.json"

with zipfile.ZipFile(ZIP_FILE, "r") as z:

    data = json.loads(z.read(COMPANY_FILE))

us_gaap = data["facts"]["us-gaap"]

# Revenue concepts we want to inspect
REVENUE_TAGS = [
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Revenues",
    "SalesRevenueNet"
]

for tag in REVENUE_TAGS:

    if tag not in us_gaap:
        print(f"\n{tag}: NOT FOUND")
        continue

    concept = us_gaap[tag]

    print("\n" + "=" * 70)
    print("TAG:", tag)
    print("LABEL:", concept.get("label"))

    units = concept.get("units", {})

    for unit, observations in units.items():

        print("UNIT:", unit)

        # Show only annual 10-K observations
        annual = [
            obs for obs in observations
            if obs.get("form") == "10-K"
            and obs.get("fp") == "FY"
        ]

        # Show latest 10 observations
        print("\nLatest annual observations:")

        for obs in annual[-10:]:
            print(
                "FY:", obs.get("fy"),
                "| Start:", obs.get("start"),
                "| End:", obs.get("end"),
                "| Value:", obs.get("val"),
                "| Filed:", obs.get("filed"),
                "| Accession:", obs.get("accn")
            )