import requests
from pathlib import Path

# FRED series that we need
SERIES = [
    "GDP",
    "GDPC1",
    "CPIAUCSL",
    "UNRATE",
    "FEDFUNDS",
    "DGS10",
    "M2SL",
    "DEXINUS"
]

# Folder where FRED data will be saved
OUTPUT_FOLDER = Path("financial_datasets/FRED")
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

print("Starting FRED downloads...\n")

for series in SERIES:

    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"

    output_file = OUTPUT_FOLDER / f"{series}.csv"

    print(f"Downloading {series}...")

    try:
        response = requests.get(url, timeout=60)

        if response.status_code == 200:

            with open(output_file, "wb") as file:
                file.write(response.content)

            print(f"  Saved: {output_file}")

        else:
            print(f"  Failed! Status code: {response.status_code}")

    except Exception as e:
        print(f"  Error: {e}")

print("\nFRED download completed!")