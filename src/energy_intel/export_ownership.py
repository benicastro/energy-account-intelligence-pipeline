"""Export EIA-860 account-level ownership evidence."""

import json
from pathlib import Path

import pandas as pd

from energy_intel.loader import load_dataset
from energy_intel.ownership_evidence import build_ownership_evidence
from energy_intel.schema import SOURCE_NAME, SOURCE_YEAR


PROJECT_ROOT = Path(__file__).resolve().parents[2]

OUTPUT_CSV = (
    PROJECT_ROOT
    / "data/processed/eia860_2025_ownership_evidence.csv"
)

OUTPUT_REPORT = (
    PROJECT_ROOT
    / "reports/eia860_2025_ownership_summary.json"
)


def export_ownership_evidence():
    """Generate ownership evidence and an audit summary."""

    print("Step 1: Loading ownership and utility datasets...")

    ownership = load_dataset("ownership")
    utilities = load_dataset("utility")

    print("Step 2: Building owner-level evidence...")

    evidence = build_ownership_evidence(
        ownership,
        utilities,
    )

    print("Step 3: Adding source metadata...")

    evidence["source_name"] = SOURCE_NAME
    evidence["source_year"] = SOURCE_YEAR
    evidence["source_table"] = "Ownership"

    evidence["evidence_status"] = (
        "Source-reported generator ownership interest"
    )

    print("Step 4: Preparing ownership summary...")

    matched = evidence["matched_to_account_master"]

    summary = {
        "source": {
            "name": SOURCE_NAME,
            "year": SOURCE_YEAR,
            "table": "Ownership",
        },
        "records": {
            "ownership_source_rows": len(ownership),
            "distinct_owner_entities": len(evidence),
            "matched_owner_accounts": int(matched.sum()),
            "unmatched_owner_entities": int((~matched).sum()),
        },
        "evidence_quality": {
            "owners_with_share_exceptions": int(
                (
                    evidence[
                        "generator_share_exception_count"
                    ] > 0
                ).sum()
            ),
            "owners_with_missing_shares": int(
                (evidence["missing_share_rows"] > 0).sum()
            ),
            "owners_with_invalid_shares": int(
                (evidence["invalid_share_rows"] > 0).sum()
            ),
            "owners_with_name_variants": int(
                (evidence["owner_name_variants"] > 1).sum()
            ),
        },
        "methodology": {
            "owner_key": "Ownership ID",
            "master_match_key": "Utility ID",
            "plant_count": "Distinct Plant Codes per owner",
            "generator_count": (
                "Distinct Plant Code + Generator ID "
                "combinations per owner"
            ),
        },
        "limitations": [
            "Ownership evidence is generator-level.",
            "A reporting utility is not necessarily the owner.",
            "No ownership record does not imply no ownership.",
            "Unmatched owners require entity verification.",
            "Generator status has not yet been used to "
            "filter active assets.",
            "Ownership shares are not aggregated into "
            "company-level ownership percentages.",
            "No sales qualification is implied.",
        ],
    }

    print("Step 5: Exporting CSV and JSON report...")

    OUTPUT_CSV.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_REPORT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    evidence = evidence.sort_values(
        by=[
            "matched_to_account_master",
            "distinct_plants_with_ownership",
            "owner_id",
        ],
        ascending=[False, False, True],
    )

    evidence.to_csv(
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

    print("Step 6: Validating exported records...")

    exported = pd.read_csv(
        OUTPUT_CSV,
        dtype="string",
        keep_default_na=False,
    )

    assert len(exported) == len(evidence)

    assert exported["owner_id"].is_unique

    assert (
        len(exported)
        == summary["records"]["distinct_owner_entities"]
    )

    assert (
        int(
            (exported["matched_to_account_master"] == "True").sum()
        )
        == summary["records"]["matched_owner_accounts"]
    )

    print("\n" + "=" * 65)
    print("OWNERSHIP EVIDENCE EXPORT COMPLETED")
    print("=" * 65)

    for key, value in summary["records"].items():
        print(f"{key}: {value:,}")

    print("\nEvidence quality:")
    for key, value in summary["evidence_quality"].items():
        print(f"  {key}: {value:,}")

    print("\nExported files:")
    print(f"  CSV: {OUTPUT_CSV}")
    print(f"  JSON: {OUTPUT_REPORT}")

    print("\nIMPORTANT")
    print("Unmatched owners have been preserved.")
    print("Original account ICP tiers remain unchanged.")

    return evidence, summary


if __name__ == "__main__":
    export_ownership_evidence()
