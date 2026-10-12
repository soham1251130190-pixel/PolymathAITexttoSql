import requests
from pathlib import Path

OUTPUT_FOLDER = Path("financial_datasets/RBI_DBIE")
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

# RBI DBIE tables
TABLES = {
    "GDP.csv":
        "https://data-api.dbie.rbihub.in/api/tables/real_sector/r822_components_of_gross_domestic_product/csv",

    "Exchange_Rates.csv":
        "https://data-api.dbie.rbihub.in/api/tables/external_sector/r1505_exchange_rate_of_the_indian_rupee_vis_vis_the_sdr_us_doll/csv",

    "Balance_of_Payments.csv":
        "https://data-api.dbie.rbihub.in/api/tables/external_sector/kci_bop_rn/csv",

    "Commercial_Bank_Survey.csv":
        "https://data-api.dbie.rbihub.in/api/tables/financial_sector/r443_commercial_bank_survey/csv"
}

print("Starting RBI DBIE downloads...\n")

for filename, url in TABLES.items():

    output_file = OUTPUT_FOLDER / filename

    print(f"Downloading {filename}...")

    try:
        response = requests.get(url, timeout=120)

        if response.status_code == 200:

            with open(output_file, "wb") as file:
                file.write(response.content)

            size_kb = output_file.stat().st_size / 1024

            print(f"  Done: {size_kb:.2f} KB")
            print(f"  Saved: {output_file}\n")

        else:
            print(f"  Failed!")
            print(f"  Status code: {response.status_code}")
            print(f"  Response: {response.text[:300]}\n")

    except Exception as e:
        print(f"  Error: {e}\n")

print("RBI DBIE download process completed!")