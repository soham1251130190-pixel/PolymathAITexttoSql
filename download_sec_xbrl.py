import requests
from pathlib import Path

# SEC XBRL Company Facts bulk dataset
URL = "https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip"

# Folder where the dataset will be saved
OUTPUT_FOLDER = Path("financial_datasets/SEC_XBRL")
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_FOLDER / "companyfacts.zip"

# Use your actual name and email
HEADERS = {
    "User-Agent": "Sparshika Wagdarkar sparshikawagdarkar@gmail.com"
}

print("Starting SEC XBRL download...")
print("Please wait. The file is large.\n")

response = requests.get(
    URL,
    headers=HEADERS,
    stream=True,
    timeout=120
)

if response.status_code != 200:
    print("Download failed!")
    print("Status code:", response.status_code)
    print(response.text[:500])
    exit()

total_size = int(response.headers.get("content-length", 0))
downloaded = 0

with open(OUTPUT_FILE, "wb") as file:
    for chunk in response.iter_content(chunk_size=1024 * 1024):
        if chunk:
            file.write(chunk)
            downloaded += len(chunk)

            if total_size:
                percentage = downloaded / total_size * 100
                print(
                    f"\rDownloaded: {percentage:.1f}%",
                    end=""
                )

print("\n\nSEC XBRL download completed!")
print(f"Saved at: {OUTPUT_FILE}")