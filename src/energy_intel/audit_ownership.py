"""Audit EIA-860 ownership relationships before joining accounts."""

import pandas as pd

from energy_intel.loader import load_dataset


def clean_id(series):
    """Keep identifiers as stripped strings."""
    return (
        series.astype("string")
        .str.strip()
        .replace("", pd.NA)
    )


def main():
    utilities = load_dataset("utility")
    ownership = load_dataset("ownership")

    account_ids = set(
        clean_id(utilities["Utility ID"]).dropna()
    )

    owner_ids = clean_id(ownership["Ownership ID"])
    reporter_ids = clean_id(ownership["Utility ID"])

    unique_owners = set(owner_ids.dropna())
    unique_reporters = set(reporter_ids.dropna())

    print("\nOWNERSHIP IDENTIFIER AUDIT")
    print("=" * 65)

    print(f"Utility master accounts: {len(account_ids):,}")
    print(f"Distinct owner IDs: {len(unique_owners):,}")
    print(f"Distinct reporting IDs: {len(unique_reporters):,}")

    print("\nOWNER-TO-ACCOUNT MATCHING")
    print("-" * 65)

    print(
        "Owner IDs found in utility master: "
        f"{len(unique_owners & account_ids):,}"
    )

    print(
        "Owner IDs absent from utility master: "
        f"{len(unique_owners - account_ids):,}"
    )

    print(
        "Ownership rows with matching account ID: "
        f"{int(owner_ids.isin(account_ids).sum()):,}"
    )

    print("\nREPORTER-TO-ACCOUNT MATCHING")
    print("-" * 65)

    print(
        "Reporting IDs found in utility master: "
        f"{len(unique_reporters & account_ids):,}"
    )

    print("\nOWNER VS REPORTER")
    print("-" * 65)

    different = owner_ids.ne(reporter_ids).fillna(False)

    print(
        "Ownership rows where owner differs from reporter: "
        f"{int(different.sum()):,}"
    )

    print(
        ownership.loc[
            different,
            [
                "Utility ID",
                "Utility Name",
                "Ownership ID",
                "Owner Name",
                "Percent Owned",
            ],
        ].head(5).to_string(index=False)
    )

    print("\nOWNERSHIP SHARE VALIDATION")
    print("-" * 65)

    shares = pd.to_numeric(
        ownership["Percent Owned"],
        errors="coerce",
    )

    print(f"Missing/non-numeric shares: {int(shares.isna().sum()):,}")
    print(
        "Shares outside 0–1: "
        f"{int(((shares < 0) | (shares > 1)).sum()):,}"
    )

    records = pd.DataFrame({
        "plant_id": clean_id(ownership["Plant Code"]),
        "generator_id": clean_id(ownership["Generator ID"]),
        "owner_id": owner_ids,
        "share": shares,
    })

    # A generator can have multiple owners. The owner ID
    # is therefore part of its ownership-record key.
    duplicate_keys = records.duplicated(
        subset=["plant_id", "generator_id", "owner_id"],
        keep=False,
    )

    print(
        "Rows with duplicate ownership keys: "
        f"{int(duplicate_keys.sum()):,}"
    )

    grouped = records.groupby(
        ["plant_id", "generator_id"],
        dropna=False,
    )["share"].agg(["sum", "count", "size"])

    complete = grouped.loc[
        grouped["count"] == grouped["size"]
    ]

    near_full = complete["sum"].between(0.99, 1.01)

    print(
        "Generator groups with numeric shares: "
        f"{len(complete):,}"
    )

    print(
        "Groups with shares summing approximately to 1: "
        f"{int(near_full.sum()):,}"
    )

    exceptions = complete.loc[~near_full]

    print(
        "Groups outside 0.99–1.01: "
        f"{len(exceptions):,}"
    )

    if not exceptions.empty:
        print("\nFirst five share-sum exceptions:")
        print(exceptions.head(5).to_string())

    print("\nIMPORTANT")
    print("-" * 65)
    print("Do not equate reporting utility with owner.")
    print("Do not count generator rows as distinct plants.")
    print("Missing ownership rows do not imply zero ownership.")
    print("Investigate exceptions before aggregating shares.")


if __name__ == "__main__":
    main()
