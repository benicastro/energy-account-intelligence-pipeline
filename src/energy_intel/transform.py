"""Transform EIA utility records into standardized accounts."""

import pandas as pd

from energy_intel.loader import load_dataset
from energy_intel.normalization import normalize_company_name
from energy_intel.schema import (
    ACCOUNT_COLUMNS,
    SOURCE_NAME,
    SOURCE_YEAR,
    UTILITY_FIELD_MAP,
)


def transform_utilities(
    utilities: pd.DataFrame,
) -> pd.DataFrame:
    """Convert EIA utility records to our account schema."""

    # Verify the required source columns exist.
    missing = set(UTILITY_FIELD_MAP) - set(utilities.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    # Rename and select fields based on our schema.
    accounts = (
        utilities.rename(columns=UTILITY_FIELD_MAP)
        [list(UTILITY_FIELD_MAP.values())]
        .copy()
    )

    # Normalize company names.
    accounts["account_name"] = (
        accounts["account_name"]
        .map(normalize_company_name)
        .astype("string")
    )

    # Remove surrounding whitespace from text fields.
    text_fields = [
        "account_id",
        "entity_type_code",
        "city",
        "state",
        "postal_code",
        "reports_plant_ownership",
        "reports_plant_operation",
    ]

    for field in text_fields:
        accounts[field] = accounts[field].str.strip()

    # Placeholder: plant counts will be calculated later.
    accounts["associated_plant_count"] = pd.Series(
        pd.NA,
        index=accounts.index,
        dtype="Int64",
    )

    # Record data provenance.
    accounts["source_year"] = SOURCE_YEAR
    accounts["source_name"] = SOURCE_NAME

    return accounts[ACCOUNT_COLUMNS]


if __name__ == "__main__":
    raw_utilities = load_dataset("utility", nrows=5)
    accounts = transform_utilities(raw_utilities)

    print("\nSTANDARDIZED ACCOUNT PREVIEW")
    print("=" * 65)

    preview_columns = [
        "account_id",
        "account_name",
        "entity_type_code",
        "state",
        "associated_plant_count",
    ]

    print(accounts[preview_columns].to_string(index=False))

    print(f"\nRecords processed: {len(accounts)}")
    print(f"Output columns: {len(accounts.columns)}")
