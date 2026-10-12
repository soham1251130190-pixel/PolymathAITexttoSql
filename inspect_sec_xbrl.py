import zipfile
import json

ZIP_FILE = "financial_datasets/SEC_XBRL/companyfacts.zip"
COMPANY_FILE = "CIK0000320193.json"

with zipfile.ZipFile(ZIP_FILE, "r") as z:

    data = json.loads(
        z.read(COMPANY_FILE)
    )

print("Company:", data["entityName"])
print("CIK:", data["cik"])

print("\nAvailable fact namespaces:")

for namespace in data["facts"]:
    print(" -", namespace)

# Look at US-GAAP concepts
us_gaap = data["facts"].get("us-gaap", {})

print("\nTotal US-GAAP concepts:", len(us_gaap))

# Search for revenue-related concepts
print("\nRevenue-related concepts:\n")

for tag, details in us_gaap.items():

    text = (
    tag + " " +
    (details.get("label") or "") + " " +
    (details.get("description") or "")
).lower()

    if "revenue" in text:

        print("TAG:", tag)
        print("LABEL:", details.get("label"))
        print("UNITS:", list(details.get("units", {}).keys()))
        print()