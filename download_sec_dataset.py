import os
import re
import io
import csv
import gzip
import shutil
import zipfile
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# ============================================================
# CONFIGURATION
# ============================================================

SEC_PAGE = "https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets"

OUTPUT_FILE = "SEC_Financial_Statements_2009_2026.csv.gz"

DOWNLOAD_DIR = "sec_downloads"
EXTRACT_DIR = "sec_extracted"

# IMPORTANT:
# Put your real identifying information here.
# SEC asks automated users to identify themselves.
USER_AGENT = "Sparshika Wagdarkar sparshikawagdarkar@gmail.com"

# Start/end years
START_YEAR = 2009
END_YEAR = 2026

# Set True if you want to keep downloaded ZIP files
KEEP_ZIPS = True

# ============================================================
# CREATE DIRECTORIES
# ============================================================

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(EXTRACT_DIR, exist_ok=True)


# ============================================================
# HTTP SESSION
# ============================================================

session = requests.Session()

session.headers.update({
    "User-Agent": USER_AGENT,
    "Accept-Encoding": "gzip, deflate",
    "Host": "www.sec.gov"
})


# ============================================================
# GET SEC DOWNLOAD LINKS
# ============================================================

print("\nReading SEC dataset page...")

response = session.get(SEC_PAGE, timeout=60)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

download_links = []

for a in soup.find_all("a", href=True):

    href = a["href"]

    if not href.lower().endswith(".zip"):
        continue

    full_url = urljoin(SEC_PAGE, href)

    # Only SEC financial statement datasets
    if "financial" in full_url.lower() or "/files/" in full_url.lower():
        download_links.append(full_url)


# Remove duplicates
download_links = sorted(set(download_links))


print(f"Found {len(download_links)} ZIP files on SEC page.")


# ============================================================
# FILTER 2009-2026
# ============================================================

def contains_target_year(url):
    match = re.search(r"(20\d{2})", url)

    if not match:
        return False

    year = int(match.group(1))

    return START_YEAR <= year <= END_YEAR


download_links = [
    url for url in download_links
    if contains_target_year(url)
]


print(f"Datasets selected: {len(download_links)}")


if len(download_links) == 0:
    raise RuntimeError(
        "No SEC dataset ZIP files were found. "
        "The SEC page structure may have changed."
    )


# ============================================================
# DOWNLOAD FUNCTION
# ============================================================

def download_file(url, destination, max_retries=8):

    # Get remote file size
    try:
        head = session.head(
            url,
            timeout=30,
            allow_redirects=True
        )

        head.raise_for_status()

        remote_size = int(
            head.headers.get("Content-Length", 0)
        )

    except Exception:
        remote_size = 0

    # Existing partial download
    existing_size = 0

    if os.path.exists(destination):
        existing_size = os.path.getsize(destination)

    # Already complete
    if remote_size > 0 and existing_size == remote_size:

        print(
            f"\nAlready complete: "
            f"{os.path.basename(destination)}"
        )

        return True

    # If existing file is somehow larger, restart it
    if remote_size > 0 and existing_size > remote_size:

        print(
            "\nExisting file is larger than remote file."
        )

        print("Starting again...")

        os.remove(destination)

        existing_size = 0

    for attempt in range(1, max_retries + 1):

        try:

            start_byte = 0

            if os.path.exists(destination):
                start_byte = os.path.getsize(destination)

            headers = {}

            if start_byte > 0:

                headers["Range"] = (
                    f"bytes={start_byte}-"
                )

                print(
                    f"\nResuming from "
                    f"{start_byte / (1024 * 1024):.2f} MB"
                )

            else:

                print("\nStarting download...")

            with session.get(
                url,
                headers=headers,
                stream=True,
                timeout=(30, 120)
            ) as r:

                # 206 = partial content
                # 200 = normal download
                if start_byte > 0 and r.status_code == 200:

                    print(
                        "\nServer did not support resume."
                    )

                    print(
                        "Restarting file..."
                    )

                    start_byte = 0

                    r.close()

                    with session.get(
                        url,
                        stream=True,
                        timeout=(30, 120)
                    ) as r2:

                        r2.raise_for_status()

                        total = int(
                            r2.headers.get(
                                "Content-Length",
                                0
                            )
                        )

                        with open(
                            destination,
                            "wb"
                        ) as f:

                            downloaded = 0

                            for chunk in r2.iter_content(
                                chunk_size=256 * 1024
                            ):

                                if chunk:

                                    f.write(chunk)

                                    downloaded += len(chunk)

                                    if total:

                                        percent = (
                                            downloaded
                                            * 100
                                            / total
                                        )

                                        print(
                                            f"\rProgress: "
                                            f"{percent:6.2f}%",
                                            end=""
                                        )

                    print(
                        "\nDownload complete."
                    )

                    return True

                r.raise_for_status()

                total_remaining = int(
                    r.headers.get(
                        "Content-Length",
                        0
                    )
                )

                total = (
                    start_byte
                    + total_remaining
                    if total_remaining
                    else remote_size
                )

                mode = (
                    "ab"
                    if start_byte > 0
                    else "wb"
                )

                downloaded = start_byte

                with open(
                    destination,
                    mode
                ) as f:

                    for chunk in r.iter_content(
                        chunk_size=256 * 1024
                    ):

                        if chunk:

                            f.write(chunk)

                            downloaded += len(chunk)

                            if total:

                                percent = (
                                    downloaded
                                    * 100
                                    / total
                                )

                                print(
                                    f"\rProgress: "
                                    f"{percent:6.2f}%",
                                    end=""
                                )

                print(
                    "\nDownload complete."
                )

                return True

        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.ChunkedEncodingError,
            requests.exceptions.ReadTimeout,
            requests.exceptions.Timeout
        ) as e:

            print(
                f"\nConnection interrupted."
            )

            print(
                f"Attempt {attempt}/{max_retries}"
            )

            if attempt < max_retries:

                wait_time = min(
                    5 * attempt,
                    30
                )

                print(
                    f"Waiting {wait_time} seconds "
                    f"before retry..."
                )

                import time

                time.sleep(wait_time)

            else:

                print(
                    "\nMaximum retries reached."
                )

                return False

        except Exception as e:

            print(
                "\nUnexpected error:"
            )

            print(e)

            return False

# ============================================================
# DOWNLOAD ALL DATASETS
# ============================================================

zip_files = []

for i, url in enumerate(download_links, start=1):

    filename = url.split("/")[-1]

    destination = os.path.join(
        DOWNLOAD_DIR,
        filename
    ) 

    print(
        f"\n[{i}/{len(download_links)}]"
    )

    success = download_file(
    url,
    destination
)

if success:
    zip_files.append(destination)
else:
    print(
        f"\nFAILED: {url}"
    )


# ============================================================
# EXTRACT DATASET
# ============================================================

def extract_zip(zip_path):

    name = os.path.splitext(
        os.path.basename(zip_path)
    )[0]

    output_folder = os.path.join(
        EXTRACT_DIR,
        name
    )

    os.makedirs(
        output_folder,
        exist_ok=True
    )

    # Avoid extracting again
    marker = os.path.join(
        output_folder,
        ".extracted"
    )

    if os.path.exists(marker):

        print(
            f"Already extracted: {name}"
        )

        return output_folder

    print(
        f"\nExtracting: {name}"
    )

    with zipfile.ZipFile(zip_path, "r") as z:

        z.extractall(output_folder)

    open(marker, "w").close()

    return output_folder


# ============================================================
# FIND FILES INSIDE DATASET
# ============================================================

def find_file(folder, filename):

    for root, dirs, files in os.walk(folder):

        for file in files:

            if file.lower() == filename.lower():

                return os.path.join(
                    root,
                    file
                )

    return None


# ============================================================
# READ TSV
# ============================================================

def read_tsv(path):

    if path is None:
        return None

    return pd.read_csv(
        path,
        sep="\t",
        dtype=str,
        low_memory=False,
        encoding="utf-8",
        on_bad_lines="skip"
    )


# ============================================================
# SELECT USEFUL SUB COLUMNS
# ============================================================

SUB_COLUMNS = [
    "adsh",
    "cik",
    "name",
    "sic",
    "countryba",
    "stprba",
    "cityba",
    "zipba",
    "form",
    "fy",
    "fp",
    "filed",
    "accepted",
    "period",
    "fy",
    "fp"
]


# ============================================================
# SELECT USEFUL NUM COLUMNS
# ============================================================

NUM_COLUMNS = [
    "adsh",
    "tag",
    "version",
    "ddate",
    "qtrs",
    "uom",
    "coreg",
    "value",
    "footnote"
]


# ============================================================
# SELECT USEFUL TAG COLUMNS
# ============================================================

TAG_COLUMNS = [
    "tag",
    "version",
    "custom",
    "abstract",
    "datatype",
    "iord",
    "crdr",
    "tlabel",
    "doc"
]


# ============================================================
# SELECT USEFUL PRE COLUMNS
# ============================================================

PRE_COLUMNS = [
    "adsh",
    "report",
    "line",
    "stmt",
    "inpth",
    "rfile",
    "tag",
    "version",
    "plabel"
]


# ============================================================
# NORMALIZE COLUMNS
# ============================================================

def keep_existing(df, columns):

    if df is None:
        return None

    existing = [
        c for c in columns
        if c in df.columns
    ]

    return df[existing].copy()


# ============================================================
# PROCESS ONE DATASET
# ============================================================

def process_dataset(zip_path, output_writer):

    dataset_name = os.path.splitext(
        os.path.basename(zip_path)
    )[0]

    print("\n")
    print("=" * 70)
    print("PROCESSING:", dataset_name)
    print("=" * 70)

    extracted = extract_zip(zip_path)

    # --------------------------------------------------------
    # Locate SEC files
    # --------------------------------------------------------

    sub_path = find_file(
        extracted,
        "sub.tsv"
    )

    num_path = find_file(
        extracted,
        "num.tsv"
    )

    tag_path = find_file(
        extracted,
        "tag.tsv"
    )

    pre_path = find_file(
        extracted,
        "pre.tsv"
    )

    if not sub_path:
        print("SUB file not found. Skipping.")
        return

    if not num_path:
        print("NUM file not found. Skipping.")
        return

    # --------------------------------------------------------
    # Read SUB
    # --------------------------------------------------------

    print("Reading SUB...")

    sub = read_tsv(sub_path)

    sub = keep_existing(
        sub,
        SUB_COLUMNS
    )

    # Remove duplicated column names if any
    sub = sub.loc[
        :,
        ~sub.columns.duplicated()
    ]

    # --------------------------------------------------------
    # Read NUM
    # --------------------------------------------------------

    print("Reading NUM...")

    num = read_tsv(num_path)

    num = keep_existing(
        num,
        NUM_COLUMNS
    )

    # --------------------------------------------------------
    # Merge NUM + SUB
    # --------------------------------------------------------

    print("Joining NUM + SUB...")

    merged = num.merge(
        sub,
        on="adsh",
        how="left",
        suffixes=("", "_sub")
    )

    del num
    del sub

    # --------------------------------------------------------
    # Read TAG
    # --------------------------------------------------------

    if tag_path:

        print("Reading TAG...")

        tag = read_tsv(tag_path)

        tag = keep_existing(
            tag,
            TAG_COLUMNS
        )

        # TAG can be joined using tag + version
        if (
            "tag" in tag.columns
            and "version" in tag.columns
            and "tag" in merged.columns
            and "version" in merged.columns
        ):

            print(
                "Joining TAG information..."
            )

            merged = merged.merge(
                tag,
                on=["tag", "version"],
                how="left",
                suffixes=("", "_tag")
            )

        del tag

    # --------------------------------------------------------
    # Read PRE
    # --------------------------------------------------------

    if pre_path:

        print("Reading PRE...")

        pre = read_tsv(pre_path)

        pre = keep_existing(
            pre,
            PRE_COLUMNS
        )

        # PRE can have multiple rows for same tag,
        # so avoid creating an enormous many-to-many merge.
        #
        # We first keep one presentation record for
        # each accession/tag/version combination.

        if (
            "adsh" in pre.columns
            and "tag" in pre.columns
            and "version" in pre.columns
        ):

            pre_small = (
                pre
                .sort_values(
                    ["adsh", "report", "line"],
                    na_position="last"
                )
                .drop_duplicates(
                    subset=[
                        "adsh",
                        "tag",
                        "version"
                    ],
                    keep="first"
                )
            )

            print(
                "Joining PRE presentation information..."
            )

            merged = merged.merge(
                pre_small,
                on=[
                    "adsh",
                    "tag",
                    "version"
                ],
                how="left",
                suffixes=("", "_pre")
            )

            del pre_small

        del pre

    # --------------------------------------------------------
    # Add dataset period
    # --------------------------------------------------------

    merged["dataset"] = dataset_name

    # --------------------------------------------------------
    # Reorder columns
    # --------------------------------------------------------

    preferred_order = [

        # Company / filing
        "cik",
        "name",
        "sic",
        "countryba",
        "stprba",
        "cityba",
        "zipba",

        # Filing
        "adsh",
        "form",
        "filed",
        "accepted",
        "period",
        "fy",
        "fp",

        # Financial fact
        "tag",
        "version",
        "value",
        "uom",
        "ddate",
        "qtrs",
        "coreg",
        "footnote",

        # Tag meaning
        "tlabel",
        "doc",
        "datatype",
        "custom",
        "abstract",
        "iord",
        "crdr",

        # Presentation
        "stmt",
        "report",
        "line",
        "plabel",
        "inpth",
        "rfile",

        # Dataset
        "dataset"
    ]

    existing_order = [
        c for c in preferred_order
        if c in merged.columns
    ]

    remaining = [
        c for c in merged.columns
        if c not in existing_order
    ]

    merged = merged[
        existing_order + remaining
    ]

    # --------------------------------------------------------
    # Clean obvious whitespace
    # --------------------------------------------------------

    for col in merged.columns:

        if merged[col].dtype == "object":

            merged[col] = (
                merged[col]
                .astype(str)
                .str.strip()
            )

    # --------------------------------------------------------
    # WRITE TO COMPRESSED CSV
    # --------------------------------------------------------

    print(
        f"Writing {len(merged):,} rows..."
    )

    merged.to_csv(
        output_writer,
        index=False,
        header=not output_writer.header_written
    )

    output_writer.header_written = True

    print(
        f"Finished {dataset_name}: "
        f"{len(merged):,} rows"
    )

    del merged


# ============================================================
# CUSTOM CSV GZIP WRITER
# ============================================================

class CSVGzipWriter:

    def __init__(self, filename):

        self.file = gzip.open(
            filename,
            "wt",
            encoding="utf-8",
            newline=""
        )

        self.header_written = False

    def write(self, data):

        self.file.write(data)

    def flush(self):

        self.file.flush()

    def close(self):

        self.file.close()


# ============================================================
# MAIN PROCESS
# ============================================================

def main():

    print("\n")
    print("=" * 70)
    print("SEC FINANCIAL STATEMENTS DATASET BUILDER")
    print("=" * 70)

    print(
        f"\nOutput: {OUTPUT_FILE}"
    )

    print(
        "\nThis may require several GB of disk space "
        "for downloads and extraction."
    )

    writer = CSVGzipWriter(
        OUTPUT_FILE
    )

    try:

        for index, zip_path in enumerate(
            zip_files,
            start=1
        ):

            print(
                f"\nDATASET {index}/{len(zip_files)}"
            )

            try:

                process_dataset(
                    zip_path,
                    writer
                )

            except Exception as e:

                print(
                    "\nERROR PROCESSING:"
                )

                print(
                    zip_path
                )

                print(
                    "Error:",
                    str(e)
                )

                print(
                    "Continuing with next dataset..."
                )

    finally:

        writer.close()

    # --------------------------------------------------------
    # DELETE ZIP FILES IF REQUESTED
    # --------------------------------------------------------

    if not KEEP_ZIPS:

        print(
            "\nDeleting downloaded ZIP files..."
        )

        for path in zip_files:

            try:

                os.remove(path)

            except OSError:
                pass

    print("\n")
    print("=" * 70)
    print("COMPLETE")
    print("=" * 70)

    print(
        f"\nCreated:\n{OUTPUT_FILE}"
    )

    print(
        "\nYou can open it with pandas using:"
    )

    print(
        "pd.read_csv("
        f"'{OUTPUT_FILE}', "
        "compression='gzip'"
        ")"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()