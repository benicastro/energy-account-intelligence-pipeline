"""Reconcile exported ownership and account intelligence datasets."""

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"


def read_csv(filename):
    return pd.read_csv(
        PROCESSED / filename,
        dtype="string",
        keep_default_na=False,
    )


def unique_ids(data, column):
    values = data[column].astype("string").str.strip()

    assert values.notna().all(), f"Null {column}"
    assert values.ne("").all(), f"Blank {column}"
    assert values.is_unique, f"Duplicate {column}"

    return set(values)


def main():
    accounts = read_csv(
        "eia860_2025_accounts_review.csv"
    )
    owners = read_csv(
        "eia860_2025_ownership_evidence.csv"
    )
    linked = read_csv(
        "eia860_2025_accounts_with_ownership.csv"
    )
    unmatched = read_csv(
        "eia860_2025_unmatched_owners.csv"
    )

    with (
        REPORTS / "eia860_2025_ownership_linkage_summary.json"
    ).open(encoding="utf-8") as file:
        summary = json.load(file)

    account_ids = unique_ids(accounts, "account_id")
    owner_ids = unique_ids(owners, "owner_id")
    linked_ids = unique_ids(linked, "account_id")
    unmatched_ids = unique_ids(unmatched, "owner_id")

    matched_ids = account_ids & owner_ids

    # Every original account must be preserved.
    assert linked_ids == account_ids

    # All owners must be accounted for exactly once.
    assert unmatched_ids == owner_ids - account_ids

    # Match statuses must agree with the identifiers.
    matched_rows = linked[
        linked["account_id"].isin(matched_ids)
    ]

    other_rows = linked[
        ~linked["account_id"].isin(matched_ids)
    ]

    assert (
        matched_rows["ownership_evidence_status"]
        == "source_reported_owner_match"
    ).all()

    assert (
        other_rows["ownership_evidence_status"]
        == "no_matched_record_in_ownership_table"
    ).all()

    assert (
        matched_rows["account_id"]
        == matched_rows["owner_id"]
    ).all()

    # Missing evidence must not be recorded as zero.
    assert other_rows["owner_id"].eq("").all()

    assert other_rows[
        "distinct_plants_with_ownership"
    ].eq("").all()

    # Ownership counts must match the original evidence.
    owner_lookup = owners.set_index("owner_id")
    matched_lookup = matched_rows.set_index("owner_id")

    for column in [
        "ownership_record_count",
        "distinct_plants_with_ownership",
        "distinct_generators_with_ownership",
        "generator_share_exception_count",
    ]:
        actual = matched_lookup[column].to_dict()
        expected = owner_lookup.loc[
            matched_lookup.index, column
        ].to_dict()

        assert actual == expected, (
            f"Ownership mismatch: {column}"
        )

    # Linking ownership must not change ICP decisions.
    original_tiers = dict(
        zip(accounts["account_id"], accounts["icp_tier"])
    )

    linked_tiers = dict(
        zip(linked["account_id"], linked["icp_tier"])
    )

    assert original_tiers == linked_tiers

    # Reconcile with the published summary.
    expected_counts = {
        "source_accounts": len(accounts),
        "source_owner_entities": len(owners),
        "linked_account_rows": len(linked),
        "accounts_with_owner_matches": len(matched_ids),
        "accounts_without_owner_matches": len(other_rows),
        "unmatched_owner_entities": len(unmatched),
    }

    for key, expected in expected_counts.items():
        assert summary[key] == expected, (
            f"Report mismatch: {key}"
        )

    print("\nOWNERSHIP LINKAGE VALIDATION")
    print("=" * 60)

    for key, count in expected_counts.items():
        print(f"{key}: {count:,}")

    print("\nAll ownership reconciliation checks PASSED.")
    print("Account ICP classifications remain unchanged.")
    print("No unmatched owner entities were discarded.")


if __name__ == "__main__":
    main()
