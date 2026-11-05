"""Tests for linking EIA ownership evidence to accounts."""

import pandas as pd
import pytest

from energy_intel.ownership_linkage import (
    link_ownership_to_accounts,
)


@pytest.fixture
def sample_tables():
    """Create fictional account and ownership records."""

    accounts = pd.DataFrame({
        "account_id": ["100", "200", "300"],
        "account_name": [
            "Alpha Energy",
            "Beta Power",
            "Gamma Utilities",
        ],
        "icp_tier": [
            "Tier 1 - Preliminary",
            "Tier 2 - Preliminary",
            "Needs Research",
        ],
    })

    ownership = pd.DataFrame({
        "owner_id": ["100", "400"],
        "source_owner_name": [
            "Alpha Energy",
            "Delta Generation",
        ],
        "ownership_record_count": ["3", "2"],
        "distinct_plants_with_ownership": ["2", "1"],
        "distinct_generators_with_ownership": ["3", "2"],
        "reporting_utility_count": ["2", "1"],
        "generator_share_exception_count": ["0", "1"],
        "missing_share_rows": ["0", "0"],
        "invalid_share_rows": ["0", "0"],
    })

    return accounts, ownership


def test_exact_id_matching_and_unmatched_owners(sample_tables):
    accounts, ownership = sample_tables

    linked, unmatched = link_ownership_to_accounts(
        accounts, ownership
    )

    by_id = linked.set_index("account_id")

    assert (
        by_id.loc["100", "ownership_evidence_status"]
        == "source_reported_owner_match"
    )

    assert (
        by_id.loc["200", "ownership_evidence_status"]
        == "no_matched_record_in_ownership_table"
    )

    # Delta is an owner but not an existing account.
    assert set(unmatched["owner_id"]) == {"400"}

    # Delta must not be assigned to another account.
    assert "400" not in set(linked["owner_id"].dropna())


def test_preserves_all_accounts_and_icp_tiers(sample_tables):
    accounts, ownership = sample_tables

    linked, _ = link_ownership_to_accounts(
        accounts, ownership
    )

    assert len(linked) == len(accounts)
    assert set(linked["account_id"]) == set(accounts["account_id"])

    original_tiers = (
        accounts.set_index("account_id")["icp_tier"].to_dict()
    )

    linked_tiers = (
        linked.set_index("account_id")["icp_tier"].to_dict()
    )

    assert linked_tiers == original_tiers


def test_missing_evidence_is_not_zero(sample_tables):
    accounts, ownership = sample_tables

    linked, _ = link_ownership_to_accounts(
        accounts, ownership
    )

    by_id = linked.set_index("account_id")

    # No owner match means unknown, not zero assets.
    assert pd.isna(
        by_id.loc["200", "distinct_plants_with_ownership"]
    )

    assert pd.isna(
        by_id.loc["300", "distinct_generators_with_ownership"]
    )

    # A matched owner's actual zero exception count is retained.
    assert (
        by_id.loc["100", "generator_share_exception_count"]
        == 0
    )

    assert str(
        linked["distinct_plants_with_ownership"].dtype
    ) == "Int64"


def test_normalizes_identifier_whitespace(sample_tables):
    accounts, ownership = sample_tables

    accounts.loc[0, "account_id"] = " 100 "
    ownership.loc[0, "owner_id"] = " 100 "

    linked, unmatched = link_ownership_to_accounts(
        accounts, ownership
    )

    assert linked.loc[0, "account_id"] == "100"
    assert linked.loc[0, "owner_id"] == "100"

    assert len(unmatched) == 1


def test_inputs_are_not_modified(sample_tables):
    accounts, ownership = sample_tables

    original_accounts = accounts.copy(deep=True)
    original_ownership = ownership.copy(deep=True)

    link_ownership_to_accounts(accounts, ownership)

    pd.testing.assert_frame_equal(
        accounts, original_accounts
    )

    pd.testing.assert_frame_equal(
        ownership, original_ownership
    )


@pytest.mark.parametrize(
    "table_name",
    ["accounts", "ownership"],
)
def test_duplicate_identifiers_raise_error(
    sample_tables, table_name
):
    accounts, ownership = sample_tables

    if table_name == "accounts":
        accounts.loc[1, "account_id"] = "100"
    else:
        ownership.loc[1, "owner_id"] = "100"

    with pytest.raises(ValueError, match="Duplicate"):
        link_ownership_to_accounts(
            accounts, ownership
        )


@pytest.mark.parametrize(
    "table_name",
    ["accounts", "ownership"],
)
def test_missing_identifiers_raise_error(
    sample_tables, table_name
):
    accounts, ownership = sample_tables

    if table_name == "accounts":
        accounts.loc[0, "account_id"] = None
    else:
        ownership.loc[0, "owner_id"] = None

    with pytest.raises(ValueError, match="Missing"):
        link_ownership_to_accounts(
            accounts, ownership
        )


@pytest.mark.parametrize(
    "table_name, column",
    [
        ("accounts", "account_id"),
        ("ownership", "owner_id"),
        ("ownership", "distinct_plants_with_ownership"),
    ],
)
def test_missing_required_columns_raise_error(
    sample_tables, table_name, column
):
    accounts, ownership = sample_tables

    if table_name == "accounts":
        accounts = accounts.drop(columns=[column])
    else:
        ownership = ownership.drop(columns=[column])

    with pytest.raises(ValueError, match="Missing"):
        link_ownership_to_accounts(
            accounts, ownership
        )
