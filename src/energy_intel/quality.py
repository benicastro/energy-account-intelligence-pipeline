"""Data quality checks for standardized energy accounts."""

import pandas as pd

from energy_intel.loader import load_dataset
from energy_intel.transform import transform_utilities
from energy_intel.association import add_plant_counts


QUALITY_FLAGS = [
    "missing_account_id",
    "missing_account_name",
    "missing_state",
    "duplicate_account_id",
]


def flag_account_quality(
    accounts: pd.DataFrame,
) -> pd.DataFrame:
    """Flag incomplete and potentially duplicate accounts.

    Does not delete records or modify the source DataFrame.
    """

    required_columns = {
        "account_id",
        "account_name",
        "state",
    }

    missing_columns = required_columns - set(accounts.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    result = accounts.copy()

    # Standardize values for quality checks.
    # Keep IDs as strings to preserve leading zeros.
    account_ids = (
        result["account_id"]
        .astype("string")
        .str.strip()
        .replace("", pd.NA)
    )

    account_names = (
        result["account_name"]
        .astype("string")
        .str.strip()
        .replace("", pd.NA)
    )

    states = (
        result["state"]
        .astype("string")
        .str.strip()
        .replace("", pd.NA)
    )

    # Check completeness.
    result["missing_account_id"] = account_ids.isna()
    result["missing_account_name"] = account_names.isna()
    result["missing_state"] = states.isna()

    # Flag repeated nonblank IDs without deleting them.
    result["duplicate_account_id"] = (
        account_ids.notna()
        & account_ids.duplicated(keep=False)
    )

    # Count the issues identified for each record.
    result["quality_issue_count"] = (
        result[QUALITY_FLAGS]
        .sum(axis=1)
        .astype("int64")
    )

    # Passing basic checks does not mean full CRM verification.
    result["quality_status"] = "no_basic_flags"

    result.loc[
        result["quality_issue_count"] > 0,
        "quality_status"
    ] = "review_required"

    return result


if __name__ == "__main__":
    print("Loading EIA utility and plant datasets...")

    utilities = load_dataset("utility")
    plants = load_dataset("plant")

    print("Building standardized accounts...")

    accounts = transform_utilities(utilities)
    accounts = add_plant_counts(accounts, plants)

    print("Running data quality checks...")

    audited = flag_account_quality(accounts)

    print("\nDATA QUALITY SUMMARY")
    print("=" * 55)

    print(f"Total accounts: {len(audited):,}")

    print(
        "No basic flags: "
        f"{(audited['quality_status'] == 'no_basic_flags').sum():,}"
    )

    print(
        "Records requiring review: "
        f"{(audited['quality_status'] == 'review_required').sum():,}"
    )

    print("\nISSUES BY CATEGORY")
    print("-" * 55)

    for flag in QUALITY_FLAGS:
        print(f"{flag}: {audited[flag].sum():,}")

    print("\nSAMPLE RECORDS REQUIRING REVIEW")
    print("-" * 55)

    review_records = audited.loc[
        audited["quality_status"] == "review_required",
        [
            "account_id",
            "account_name",
            "state",
            "quality_issue_count",
        ],
    ].head(10)

    if review_records.empty:
        print("No issues found by the current checks.")
    else:
        print(review_records.to_string(index=False))
