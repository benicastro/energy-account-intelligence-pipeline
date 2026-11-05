"""Associate EIA utility accounts with reported power plants."""

import pandas as pd

from energy_intel.loader import load_dataset
from energy_intel.transform import transform_utilities


def add_plant_counts(
    accounts: pd.DataFrame,
    plants: pd.DataFrame,
) -> pd.DataFrame:
    """Add distinct associated plant counts to utility accounts."""

    required_account_fields = {
        "account_id",
        "associated_plant_count",
    }
    required_plant_fields = {
        "Utility ID",
        "Plant Code",
    }

    if not required_account_fields.issubset(accounts.columns):
        raise ValueError("Missing required account columns")

    if not required_plant_fields.issubset(plants.columns):
        raise ValueError("Missing required plant columns")

    result = accounts.copy()

    # Work only with fields required for this association.
    plant_records = plants[
        ["Utility ID", "Plant Code"]
    ].copy()

    # Normalize identifiers without converting them to numbers.
    for column in plant_records.columns:
        plant_records[column] = (
            plant_records[column]
            .astype("string")
            .str.strip()
            .replace("", pd.NA)
        )

    # Records without either identifier cannot be matched.
    plant_records = plant_records.dropna(
        subset=["Utility ID", "Plant Code"]
    )

    # Count distinct plant codes for each utility.
    plant_counts = (
        plant_records
        .groupby("Utility ID")["Plant Code"]
        .nunique()
    )

    account_ids = (
        result["account_id"]
        .astype("string")
        .str.strip()
        .replace("", pd.NA)
    )

    result["associated_plant_count"] = (
        account_ids
        .map(plant_counts)
        .fillna(0)
        .astype("Int64")
        .mask(account_ids.isna(), pd.NA)
    )

    return result


if __name__ == "__main__":
    print("Loading EIA-860 utility and plant datasets...")

    utilities = load_dataset("utility")
    plants = load_dataset("plant")

    print("Transforming utility records...")
    accounts = transform_utilities(utilities)

    print("Associating reported power plants...")
    accounts = add_plant_counts(accounts, plants)

    print("\nACCOUNT INTELLIGENCE PREVIEW")
    print("=" * 75)

    preview = [
        "account_id",
        "account_name",
        "state",
        "associated_plant_count",
    ]

    print(
        accounts[preview]
        .sort_values(
            "associated_plant_count",
            ascending=False
        )
        .head(10)
        .to_string(index=False)
    )

    print("\nPIPELINE SUMMARY")
    print("-" * 40)
    print(f"Utility records: {len(utilities):,}")
    print(f"Plant records: {len(plants):,}")
    print(f"Account records: {len(accounts):,}")

    with_plants = (
        accounts["associated_plant_count"].fillna(0) > 0
    ).sum()

    print(f"Accounts with associated plants: {with_plants:,}")
