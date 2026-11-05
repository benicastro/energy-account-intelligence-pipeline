"""Reusable data loading utilities for EIA-860."""

from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pandas as pd


# Resolve the project root relative to this Python file.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_ARCHIVE = (
    PROJECT_ROOT / "data" / "raw" / "eia8602025.zip"
)

WORKBOOKS = {
    "utility": ("1___Utility_Y2025.xlsx", "Utility"),
    "plant": ("2___Plant_Y2025.xlsx", "Plant"),
    "ownership": ("4___Owner_Y2025.xlsx", "Ownership"),
}


def load_dataset(
    dataset: str,
    nrows: int | None = None,
    archive_path: Path = DEFAULT_ARCHIVE,
) -> pd.DataFrame:
    """Load a dataset from the EIA-860 ZIP archive.

    Args:
        dataset: One of 'utility', 'plant', or 'ownership'.
        nrows: Optional limit on records to load.
        archive_path: Location of the EIA-860 archive.

    Returns:
        A pandas DataFrame containing the requested data.
    """

    if dataset not in WORKBOOKS:
        raise ValueError(
            f"Unknown dataset: {dataset}. "
            f"Choose from: {', '.join(WORKBOOKS)}"
        )

    archive_path = Path(archive_path)

    if not archive_path.is_file():
        raise FileNotFoundError(
            f"EIA archive not found: {archive_path}"
        )

    filename, sheet_name = WORKBOOKS[dataset]

    with ZipFile(archive_path) as archive:
        if filename not in archive.namelist():
            raise FileNotFoundError(
                f"Workbook not found inside ZIP: {filename}"
            )

        workbook_bytes = archive.read(filename)

    dataframe = pd.read_excel(
        BytesIO(workbook_bytes),
        sheet_name=sheet_name,
        header=1,
        dtype="string",
        nrows=nrows,
    )

    return dataframe


if __name__ == "__main__":
    for dataset_name in WORKBOOKS:
        df = load_dataset(dataset_name, nrows=3)

        print(f"\nDataset: {dataset_name}")
        print(f"Rows loaded: {len(df)}")
        print(f"Columns: {len(df.columns)}")
        print("-" * 40)
