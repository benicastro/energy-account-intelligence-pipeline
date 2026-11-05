"""Run the EIA-860 account intelligence pipeline."""

import json
from pathlib import Path

from energy_intel.loader import load_dataset
from energy_intel.transform import transform_utilities
from energy_intel.association import add_plant_counts
from energy_intel.quality import (
    QUALITY_FLAGS,
    flag_account_quality,
)
from energy_intel.schema import SOURCE_NAME, SOURCE_YEAR
from energy_intel.classification import classify_accounts


PROJECT_ROOT = Path(__file__).resolve().parents[2]

OUTPUT_CSV = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "eia860_2025_accounts_review.csv"
)

OUTPUT_REPORT = (
    PROJECT_ROOT
    / "reports"
    / "eia860_2025_quality_summary.json"
)


def run_pipeline():
    """Build, audit, and export standardized account data."""

    print("Step 1: Loading source datasets...")
    utilities = load_dataset("utility")
    plants = load_dataset("plant")

    print("Step 2: Standardizing utility accounts...")
    accounts = transform_utilities(utilities)

    print("Step 3: Calculating plant associations...")
    accounts = add_plant_counts(accounts, plants)

    print("Step 4: Running data-quality checks...")
    accounts = flag_account_quality(accounts)

    print("Step 5: Applying preliminary ICP classification...")
    accounts = classify_accounts(accounts)

    print("Step 6: Preparing quality summary...")

    icp_counts = {
        str(tier): int(count)
        for tier, count in accounts["icp_tier"].value_counts().items()
    }

    issue_counts = {
        flag: int(accounts[flag].sum())
        for flag in QUALITY_FLAGS
    }

    review_count = int(
        (accounts["quality_status"] == "review_required").sum()
    )

    accounts_with_plants = int(
        (accounts["associated_plant_count"].fillna(0) > 0).sum()
    )

    summary = {
        "source": {
            "name": SOURCE_NAME,
            "year": SOURCE_YEAR,
            "source_type": "Public EIA-860 annual dataset",
        },
        "records": {
            "utility_source_rows": len(utilities),
            "plant_source_rows": len(plants),
            "account_output_rows": len(accounts),
            "accounts_with_associated_plants": accounts_with_plants,
        },
        "data_quality": {
            "records_requiring_review": review_count,
            "records_without_basic_flags": (
                len(accounts) - review_count
            ),
            "issues_by_category": issue_counts,
        },
        "icp_classification": {
            "rule_version": "1.0",
            "preliminary_tier_counts": icp_counts,
            "warning": (
                "Preliminary research classification only. "
                "Not verified sales-qualified accounts."
            ),
        },
        "limitations": [
            "Plant associations do not establish ownership.",
            "Duplicate identifiers are flagged, not removed.",
            "No contact enrichment has been performed.",
            "No basic flags does not imply CRM verification.",
            "ICP tiers are preliminary and require further verification.",
        ],
    }

    print("Step 7: Exporting results...")

    OUTPUT_CSV.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_REPORT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    accounts.to_csv(
        OUTPUT_CSV,
        index=False,
        encoding="utf-8-sig",
    )

    with OUTPUT_REPORT.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            summary,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 60)

    print(f"Accounts exported: {len(accounts):,}")
    print(f"Accounts with plants: {accounts_with_plants:,}")
    print(f"Records requiring review: {review_count:,}")

    print("\nQuality issues:")
    for flag, count in issue_counts.items():
        print(f"  {flag}: {count:,}")

    print("\nOutput files:")
    print(f"  CSV: {OUTPUT_CSV}")
    print(f"  Report: {OUTPUT_REPORT}")

    return accounts, summary


if __name__ == "__main__":
    run_pipeline()
