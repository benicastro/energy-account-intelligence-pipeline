
"""Inspect EIA-860 utility, plant, and ownership datasets."""

from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pandas as pd


ARCHIVE_PATH = Path("data/raw/eia8602025.zip")

WORKBOOKS = {
    "Utility": ("1___Utility_Y2025.xlsx", "Utility"),
    "Plant": ("2___Plant_Y2025.xlsx", "Plant"),
    "Ownership": ("4___Owner_Y2025.xlsx", "Ownership"),
}


def main():
    with ZipFile(ARCHIVE_PATH) as archive:
        for label, (filename, sheet_name) in WORKBOOKS.items():

            with archive.open(filename) as file:
                dataframe = pd.read_excel(
                    BytesIO(file.read()),
                    sheet_name=sheet_name,
                    header=1,
                    nrows=5,
                    dtype=str,
                )

            print(f"\n{'=' * 65}")
            print(f"DATASET: {label}")
            print(f"Preview rows loaded: {len(dataframe)}")
            print(f"Total columns: {len(dataframe.columns)}")

            print("\nFirst 15 column names:")
            for column in dataframe.columns[:15]:
                print(f"  - {column}")

            print("\nFirst 3 records (first 7 columns):")
            print(
                dataframe.iloc[:3, :7]
                .fillna("")
                .to_string(index=False)
            )


if __name__ == "__main__":
    main()
