"""Inspect EIA-860 generator ownership records."""

import pandas as pd

from energy_intel.loader import load_dataset


def main():
    ownership = load_dataset("ownership")

    print("\nEIA-860 GENERATOR OWNERSHIP PROFILE")
    print("=" * 65)

    print(f"Total ownership records: {len(ownership):,}")

    print("\nAVAILABLE COLUMNS")
    print("-" * 65)

    for column in ownership.columns:
        print(f"  {column}")

    print("\nIDENTIFIER COVERAGE")
    print("-" * 65)

    for column in [
        "Utility ID",
        "Plant Code",
        "Generator ID",
        "Owner Name",
        "Ownership ID",
    ]:
        values = (
            ownership[column]
            .astype("string")
            .str.strip()
            .replace("", pd.NA)
        )

        print(
            f"{column}: "
            f"{values.nunique():,} distinct; "
            f"{values.isna().sum():,} missing"
        )

    print("\nGENERATOR STATUS DISTRIBUTION")
    print("-" * 65)

    statuses = (
        ownership["Status"]
        .astype("string")
        .str.strip()
        .fillna("(missing)")
        .replace("", "(blank)")
    )

    print(statuses.value_counts().to_string())

    print("\nOWNERSHIP PERCENTAGE VALUES")
    print("-" * 65)

    percentages = (
        ownership["Percent Owned"]
        .astype("string")
        .str.strip()
        .fillna("(missing)")
        .replace("", "(blank)")
    )

    print("Most frequent values:")
    print(percentages.value_counts().head(15).to_string())

    print("\nSAMPLE OWNERSHIP RECORDS")
    print("-" * 65)

    selected_columns = [
        "Utility ID",
        "Utility Name",
        "Plant Code",
        "Generator ID",
        "Status",
        "Owner Name",
        "Ownership ID",
        "Percent Owned",
    ]

    print(
        ownership[selected_columns]
        .head(8)
        .fillna("(missing)")
        .to_string(index=False)
    )

    print("\nIMPORTANT")
    print("-" * 65)
    print("Ownership records are generator-level.")
    print("Multiple rows for one plant may be legitimate.")
    print("Owner identifiers and percentage values must be")
    print("interpreted before account-level aggregation.")


if __name__ == "__main__":
    main()
