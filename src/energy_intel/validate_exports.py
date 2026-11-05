"""Validate the exported EIA account dataset and quality report."""

import json
from pathlib import Path

import pandas as pd

from energy_intel.quality import QUALITY_FLAGS
from energy_intel.schema import ACCOUNT_COLUMNS


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CSV_PATH = (
    PROJECT_ROOT
    / "data/processed/eia860_2025_accounts_review.csv"
)

REPORT_PATH = (
    PROJECT_ROOT
    / "reports/eia860_2025_quality_summary.json"
)


def validate_exports():
    """Reconcile CSV contents with reported quality metrics."""

    accounts = pd.read_csv(
        CSV_PATH,
        dtype="string",
        keep_default_na=False,
    )

    with REPORT_PATH.open(encoding="utf-8") as file:
        report = json.load(file)

    # 1. Verify the exported column structure.
    expected_columns = (
        ACCOUNT_COLUMNS
        + QUALITY_FLAGS
        + ["quality_issue_count", "quality_status"]
        + [
            "entity_type_description",
            "icp_tier",
            "icp_rationale",
            "icp_rule_version",
            "icp_source_year",
        ]
    )

    assert list(accounts.columns) == expected_columns, (
        "CSV columns do not match the expected schema."
    )

    # 2. Verify the exported row count.
    expected_rows = report["records"]["account_output_rows"]

    assert len(accounts) == expected_rows, (
        "CSV row count does not match the quality report."
    )

    # 3. Recalculate quality flags from the CSV.
    flag_values = {}

    for flag in QUALITY_FLAGS:
        values = accounts[flag]

        assert values.isin(["True", "False"]).all(), (
            f"Unexpected values in {flag}"
        )

        flag_values[flag] = values.eq("True")

        actual_count = int(flag_values[flag].sum())

        reported_count = (
            report["data_quality"]["issues_by_category"][flag]
        )

        assert actual_count == reported_count, (
            f"Quality count mismatch: {flag}"
        )

    # 4. Verify the issue count for every record.
    calculated_issues = pd.DataFrame(
        flag_values
    ).sum(axis=1)

    exported_issues = pd.to_numeric(
        accounts["quality_issue_count"],
        errors="raise",
    )

    assert (
        calculated_issues == exported_issues
    ).all(), "Per-record quality counts do not match."

    # 5. Verify review statuses.
    expected_status = calculated_issues.map(
        lambda count: (
            "review_required"
            if count > 0
            else "no_basic_flags"
        )
    )

    assert (
        accounts["quality_status"] == expected_status
    ).all(), "Quality statuses are inconsistent."

    review_count = int(
        (expected_status == "review_required").sum()
    )

    assert review_count == (
        report["data_quality"]["records_requiring_review"]
    )

    assert len(accounts) - review_count == (
        report["data_quality"]["records_without_basic_flags"]
    )

    # 6. Reconcile plant association counts.
    plant_counts = pd.to_numeric(
        accounts["associated_plant_count"].replace("", pd.NA),
        errors="raise",
    )

    accounts_with_plants = int(
        (plant_counts.fillna(0) > 0).sum()
    )

    assert accounts_with_plants == (
        report["records"]["accounts_with_associated_plants"]
    )

    # Reconcile preliminary ICP counts with the report.
    actual_tiers = {
        str(tier): int(count)
        for tier, count in accounts["icp_tier"].value_counts().items()
    }

    reported_tiers = report[
        "icp_classification"
    ]["preliminary_tier_counts"]

    assert actual_tiers == reported_tiers, (
        "ICP classification counts do not match the report."
    )

    print("\nEXPORT VALIDATION RESULTS")
    print("=" * 50)
    print(f"CSV rows validated: {len(accounts):,}")
    print(f"Columns validated: {len(accounts.columns)}")
    print(f"Accounts with plants: {accounts_with_plants:,}")
    print(f"Records requiring review: {review_count:,}")
    print("\nAll export reconciliation checks PASSED.")


if __name__ == "__main__":
    validate_exports()
