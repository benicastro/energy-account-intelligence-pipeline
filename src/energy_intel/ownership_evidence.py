"""Build account-level evidence from EIA generator ownership records."""

import pandas as pd

from energy_intel.loader import load_dataset


def clean_id(values):
    return (
        values.astype("string")
        .str.strip()
        .replace("", pd.NA)
    )


def build_ownership_evidence(ownership, utilities):
    """Summarize ownership by owner ID without dropping unmatched owners."""

    required_ownership = {
        "Ownership ID", "Owner Name", "Utility ID",
        "Plant Code", "Generator ID", "Percent Owned",
    }

    required_utilities = {"Utility ID", "Utility Name"}

    if missing := required_ownership - set(ownership.columns):
        raise ValueError(f"Missing ownership fields: {sorted(missing)}")

    if missing := required_utilities - set(utilities.columns):
        raise ValueError(f"Missing utility fields: {sorted(missing)}")

    records = ownership.copy()

    for source, target in {
        "Ownership ID": "owner_id",
        "Owner Name": "owner_name",
        "Utility ID": "reporter_id",
        "Plant Code": "plant_id",
        "Generator ID": "generator_id",
    }.items():
        records[target] = clean_id(records[source])

    # Do not silently aggregate records without valid keys.
    keys = ["owner_id", "plant_id", "generator_id"]

    if records[keys].isna().any().any():
        raise ValueError("Missing ownership/plant/generator identifier")

    records["share"] = pd.to_numeric(
        records["Percent Owned"],
        errors="coerce",
    )

    records["missing_share"] = records["share"].isna()

    records["invalid_share"] = (
        (records["share"] < 0) | (records["share"] > 1)
    ).fillna(False)

    # Audit totals at the generator level, not plant level.
    generator_groups = records.groupby(
        ["plant_id", "generator_id"]
    )["share"]

    share_sum = generator_groups.transform("sum")
    share_count = generator_groups.transform("count")
    group_size = generator_groups.transform("size")

    records["generator_share_exception"] = (
        (share_count != group_size)
        | ~share_sum.between(0.99, 1.01)
        | records["invalid_share"]
    )

    # One row per reported owner.
    evidence = records.groupby(
        "owner_id", as_index=False
    ).agg(
        source_owner_name=("owner_name", "first"),
        owner_name_variants=("owner_name", "nunique"),
        ownership_record_count=("owner_id", "size"),
        distinct_plants_with_ownership=(
            "plant_id", "nunique"
        ),
        reporting_utility_count=("reporter_id", "nunique"),
        missing_share_rows=("missing_share", "sum"),
        invalid_share_rows=("invalid_share", "sum"),
    )

    # A Generator ID may be reused across different plants.
    generator_keys = [
        "owner_id", "plant_id", "generator_id"
    ]

    generator_counts = (
        records[generator_keys]
        .drop_duplicates()
        .groupby("owner_id")
        .size()
    )

    evidence["distinct_generators_with_ownership"] = (
        evidence["owner_id"]
        .map(generator_counts)
        .astype("int64")
    )

    exception_counts = (
        records.loc[
            records["generator_share_exception"],
            generator_keys,
        ]
        .drop_duplicates()
        .groupby("owner_id")
        .size()
    )

    evidence["generator_share_exception_count"] = (
        evidence["owner_id"]
        .map(exception_counts)
        .fillna(0)
        .astype("int64")
    )

    # Build the account lookup using EIA identifiers only.
    master = utilities[
        ["Utility ID", "Utility Name"]
    ].copy()

    master["account_id"] = clean_id(master["Utility ID"])

    if master["account_id"].duplicated().any():
        raise ValueError("Duplicate Utility IDs in account master")

    account_names = master.set_index(
        "account_id"
    )["Utility Name"]

    evidence["matched_to_account_master"] = (
        evidence["owner_id"].isin(account_names.index)
    )

    evidence["matched_account_name"] = (
        evidence["owner_id"].map(account_names)
    )

    return evidence


def main():
    ownership = load_dataset("ownership")
    utilities = load_dataset("utility")

    evidence = build_ownership_evidence(
        ownership, utilities
    )

    print("\nACCOUNT-LEVEL OWNERSHIP EVIDENCE")
    print("=" * 65)

    matched = evidence["matched_to_account_master"]

    print(f"Total owner entities: {len(evidence):,}")
    print(f"Matched accounts: {int(matched.sum()):,}")
    print(f"Unmatched owners: {int((~matched).sum()):,}")

    print(
        "Owners with generator-share exceptions: "
        f"{int((evidence['generator_share_exception_count'] > 0).sum()):,}"
    )

    print(
        "Owners with missing shares: "
        f"{int((evidence['missing_share_rows'] > 0).sum()):,}"
    )

    print("\nMATCHED OWNER EXAMPLES")
    print("-" * 65)

    columns = [
        "owner_id",
        "source_owner_name",
        "distinct_plants_with_ownership",
        "distinct_generators_with_ownership",
        "matched_account_name",
    ]

    print(
        evidence.loc[matched, columns]
        .head(5)
        .to_string(index=False)
    )

    print("\nUNMATCHED OWNER EXAMPLES")
    print("-" * 65)

    print(
        evidence.loc[~matched, columns]
        .head(5)
        .to_string(index=False)
    )

    print("\nNOTE")
    print("No ownership absence is inferred for unmatched accounts.")
    print("No ICP tiers have been modified.")
    print("Ownership-share exceptions remain flagged.")


if __name__ == "__main__":
    main()
