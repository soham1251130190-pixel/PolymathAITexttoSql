import requests
from pathlib import Path

URL = "https://databank.worldbank.org/data/download/WDI_CSV.zip"

OUTPUT_FOLDER = Path("financial_datasets/World_Bank_WDI")
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_FOLDER / "WDI_CSV.zip"

print("Starting World Bank WDI download...")
print("The file is large, so this may take some time.\n")

response = requests.get(
    URL,
    stream=True,
    timeout=600
)

if response.status_code != 200:
    print("Download failed!")
    print("Status code:", response.status_code)
    exit()

total_size = int(response.headers.get("content-length", 0))
downloaded = 0

with open(OUTPUT_FILE, "wb") as file:

    for chunk in response.iter_content(chunk_size=1024 * 1024):

        if chunk:
            file.write(chunk)
            downloaded += len(chunk)

            if total_size:
                percentage = min(downloaded / total_size * 100, 100)

                print(
                    f"\rDownloaded: {percentage:.1f}%",
                    end=""
                )

print("\n\nWorld Bank WDI download completed!")
print(f"Saved at: {OUTPUT_FILE}")

file_size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)

print(f"File size: {file_size_mb:.2f} MB")