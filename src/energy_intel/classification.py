"""Preliminary ICP classification for EIA-860 accounts."""

import pandas as pd

from energy_intel.schema import SOURCE_YEAR


# Official EIA-860 entity type definitions.
ENTITY_TYPES = {
    "Q": "Independent Power Producer",
    "M": "Municipally-Owned Utility",
    "IND": "Industrial",
    "COM": "Commercial",
    "I": "Investor-Owned Utility",
    "C": "Cooperative",
    "P": "Political Subdivision",
    "S": "State-Owned Utility",
    "F": "Federally-Owned Utility",
}

# Our own ICP research policy, not an EIA designation.
PRIMARY_CODES = {"Q", "M", "I", "C", "P", "S", "F"}
SECONDARY_CODES = {"IND", "COM"}


def classify_accounts(accounts: pd.DataFrame) -> pd.DataFrame:
    """Assign preliminary ICP tiers without modifying input."""

    required = {
        "entity_type_code",
        "associated_plant_count",
        "quality_status",
    }

    missing = required - set(accounts.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    result = accounts.copy()

    codes = (
        result["entity_type_code"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    result["entity_type_description"] = (
        codes.map(ENTITY_TYPES)
        .fillna("Unknown or missing entity type")
    )

    plant_counts = pd.to_numeric(
        result["associated_plant_count"],
        errors="coerce",
    )

    # A usable preliminary classification requires an
    # associated plant and no existing basic quality flags.
    evidence_ok = (
        plant_counts.gt(0)
        & result["quality_status"].eq("no_basic_flags")
    )

    primary = codes.isin(PRIMARY_CODES) & evidence_ok
    secondary = codes.isin(SECONDARY_CODES) & evidence_ok

    result["icp_tier"] = "Needs Research"

    result.loc[
        primary, "icp_tier"
    ] = "Tier 1 - Preliminary"

    result.loc[
        secondary, "icp_tier"
    ] = "Tier 2 - Preliminary"

    # Document the reason for each classification.
    result["icp_rationale"] = (
        "Manual review needed: missing or insufficient "
        "classification evidence."
    )

    result.loc[
        primary, "icp_rationale"
    ] = (
        "EIA entity category matches primary energy ICP; "
        "reported plant association found. "
        "Ownership and commercial fit not yet verified."
    )

    result.loc[
        secondary, "icp_rationale"
    ] = (
        "Industrial/commercial EIA entity with reported "
        "plant association. Confirm whether generation "
        "is material to the organization's business."
    )

    result["icp_rule_version"] = "1.0"
    result["icp_source_year"] = SOURCE_YEAR

    return result


if __name__ == "__main__":
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[2]

    csv_path = (
        project_root
        / "data/processed/eia860_2025_accounts_review.csv"
    )

    accounts = pd.read_csv(
        csv_path,
        dtype="string",
        keep_default_na=False,
    )

    classified = classify_accounts(accounts)

    print("\nPRELIMINARY ICP CLASSIFICATION")
    print("=" * 60)

    print(f"Total accounts: {len(classified):,}")

    print("\nClassification distribution:")
    print(
        classified["icp_tier"]
        .value_counts()
        .to_string()
    )

    print("\nENTITY TYPES BY ICP TIER")
    print("-" * 60)

    print(
        pd.crosstab(
            classified["entity_type_description"],
            classified["icp_tier"],
        ).to_string()
    )

    print("\nIMPORTANT")
    print("These are preliminary research classifications.")
    print("They are NOT verified sales-qualified accounts.")
    print("Plant associations do not prove ownership.")
    print("Geographic and operational fit remain unverified.")
