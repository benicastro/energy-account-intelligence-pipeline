
"""Link account intelligence with source-reported ownership evidence."""

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

ACCOUNTS_CSV = (
    PROJECT_ROOT
    / "data/processed/eia860_2025_accounts_review.csv"
)

OWNERSHIP_CSV = (
    PROJECT_ROOT
    / "data/processed/eia860_2025_ownership_evidence.csv"
)

LINKED_CSV = (
    PROJECT_ROOT
    / "data/processed/eia860_2025_accounts_with_ownership.csv"
)

UNMATCHED_CSV = (
    PROJECT_ROOT
    / "data/processed/eia860_2025_unmatched_owners.csv"
)

SUMMARY_JSON = (
    PROJECT_ROOT
    / "reports/eia860_2025_ownership_linkage_summary.json"
)


def clean_ids(values):
    return (
        values.astype("string")
        .str.strip()
        .replace("", pd.NA)
    )


def link_ownership_to_accounts(accounts, ownership):
    """Join on official EIA identifiers, retaining unmatched owners."""

    if "account_id" not in accounts.columns:
        raise ValueError("Missing account_id")

    if "owner_id" not in ownership.columns:
        raise ValueError("Missing owner_id")

    accounts = accounts.copy()
    ownership = ownership.copy()

    accounts["account_id"] = clean_ids(accounts["account_id"])
    ownership["owner_id"] = clean_ids(ownership["owner_id"])

    if accounts["account_id"].isna().any():
        raise ValueError("Missing account identifiers")

    if ownership["owner_id"].isna().any():
        raise ValueError("Missing owner identifiers")

    if accounts["account_id"].duplicated().any():
        raise ValueError("Duplicate account identifiers")

    if ownership["owner_id"].duplicated().any():
        raise ValueError("Duplicate owner identifiers")

    evidence_fields = [
        "owner_id",
        "source_owner_name",
        "ownership_record_count",
        "distinct_plants_with_ownership",
        "distinct_generators_with_ownership",
        "reporting_utility_count",
        "generator_share_exception_count",
        "missing_share_rows",
        "invalid_share_rows",
    ]

    missing = set(evidence_fields) - set(ownership.columns)

    if missing:
        raise ValueError(
            f"Missing ownership evidence columns: {sorted(missing)}"
        )

    # Left join: every original account remains in the output.
    linked = accounts.merge(
        ownership[evidence_fields],
        how="left",
        left_on="account_id",
        right_on="owner_id",
        validate="one_to_one",
        indicator=True,
    )

    matched = linked["_merge"].eq("both")

    linked["ownership_evidence_status"] = (
        "no_matched_record_in_ownership_table"
    )

    linked.loc[
        matched, "ownership_evidence_status"
    ] = "source_reported_owner_match"

    linked = linked.drop(columns=["_merge"])

    # Missing evidence stays missing; never replace it with 0.
    count_fields = [
        "ownership_record_count",
        "distinct_plants_with_ownership",
        "distinct_generators_with_ownership",
        "reporting_utility_count",
        "generator_share_exception_count",
        "missing_share_rows",
        "invalid_share_rows",
    ]

    for field in count_fields:
        linked[field] = pd.to_numeric(
            linked[field], errors="raise"
        ).astype("Int64")

    # Preserve owners absent from the account master.
    unmatched_owners = ownership.loc[
        ~ownership["owner_id"].isin(accounts["account_id"])
    ].copy()

    if len(linked) != len(accounts):
        raise AssertionError("Account row count changed")

    if int(matched.sum()) + len(unmatched_owners) != len(ownership):
        raise AssertionError("Ownership reconciliation failed")

    return linked, unmatched_owners


def main():
    print("Step 1: Loading existing account and ownership exports...")

    accounts = pd.read_csv(
        ACCOUNTS_CSV,
        dtype="string",
        keep_default_na=False,
    )

    ownership = pd.read_csv(
        OWNERSHIP_CSV,
        dtype="string",
        keep_default_na=False,
    )

    print("Step 2: Linking ownership by EIA identifiers...")

    linked, unmatched = link_ownership_to_accounts(
        accounts, ownership
    )

    matched = linked["ownership_evidence_status"].eq(
        "source_reported_owner_match"
    )

    print("Step 3: Preparing reconciliation summary...")

    summary = {
        "source_accounts": len(accounts),
        "source_owner_entities": len(ownership),
        "linked_account_rows": len(linked),
        "accounts_with_owner_matches": int(matched.sum()),
        "accounts_without_owner_matches": int((~matched).sum()),
        "unmatched_owner_entities": len(unmatched),
        "matching_method": "Exact EIA account_id to Ownership ID",
        "limitations": [
            "No matching ownership record does not imply no ownership.",
            "Generator-level ownership evidence is not proof of current operational status.",
            "ICP tiers have not been changed.",
            "Unmatched owners are preserved separately for research.",
        ],
    }

    print("Step 4: Exporting linked and unmatched datasets...")

    LINKED_CSV.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)

    linked.to_csv(
        LINKED_CSV,
        index=False,
        encoding="utf-8-sig",
    )

    unmatched.to_csv(
        UNMATCHED_CSV,
        index=False,
        encoding="utf-8-sig",
    )

    with SUMMARY_JSON.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)

    print("\nOWNERSHIP LINKAGE RESULTS")
    print("=" * 65)

    for key, value in summary.items():
        if isinstance(value, int):
            print(f"{key}: {value:,}")

    print("\nOwnership evidence status:")
    print(
        linked["ownership_evidence_status"]
        .value_counts()
        .to_string()
    )

    print("\nOutput files:")
    print(f"  Linked accounts: {LINKED_CSV}")
    print(f"  Unmatched owners: {UNMATCHED_CSV}")
    print(f"  Summary: {SUMMARY_JSON}")

    print("\nIMPORTANT")
    print("No existing account records were discarded.")
    print("Unmatched owners were retained separately.")
    print("Missing ownership evidence was not converted to zero.")
    print("Original ICP classifications remain unchanged.")


if __name__ == "__main__":
    main()
