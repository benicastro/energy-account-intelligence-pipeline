"""Tests for EIA-860 account-level ownership evidence."""

import pandas as pd
import pytest

from energy_intel.ownership_evidence import (
    build_ownership_evidence,
)


@pytest.fixture
def source_tables():
    """Create fictional ownership and utility records."""

    ownership = pd.DataFrame({
        "Ownership ID": [
            "100", "200", "100", "100", "300", "400"
        ],
        "Owner Name": [
            "Alpha Energy",
            "Beta Power",
            "Alpha Energy",
            "Alpha Energy",
            "Gamma Generation",
            "Delta Power",
        ],
        "Utility ID": [
            "900", "900", "900", "901", "901", "902"
        ],
        "Plant Code": [
            "10", "10", "10", "20", "30", "40"
        ],
        "Generator ID": [
            "G1", "G1", "G2", "G1", "G1", "G1"
        ],
        "Percent Owned": [
            "0.6", "0.4", "1", "1", "0.9", None
        ],
    })

    utilities = pd.DataFrame({
        "Utility ID": ["100", "900", "901", "902"],
        "Utility Name": [
            "Alpha Energy",
            "Reporting Utility A",
            "Reporting Utility B",
            "Reporting Utility C",
        ],
    })

    return ownership, utilities


def get_owner(evidence, owner_id):
    """Retrieve one owner record by identifier."""
    return evidence.set_index("owner_id").loc[owner_id]


def test_matches_using_owner_id_not_reporter(source_tables):
    ownership, utilities = source_tables

    result = build_ownership_evidence(
        ownership, utilities
    )

    alpha = get_owner(result, "100")
    beta = get_owner(result, "200")

    assert bool(alpha["matched_to_account_master"])
    assert alpha["matched_account_name"] == "Alpha Energy"

    # Reporter 900 exists in the utility master.
    # That must not cause owner 200 to match.
    assert not bool(beta["matched_to_account_master"])
    assert pd.isna(beta["matched_account_name"])


def test_counts_distinct_plants_and_generators(source_tables):
    ownership, utilities = source_tables

    result = build_ownership_evidence(
        ownership, utilities
    )

    alpha = get_owner(result, "100")

    assert alpha["ownership_record_count"] == 3
    assert alpha["distinct_plants_with_ownership"] == 2

    # Generator G1 appears in two different plants.
    assert alpha["distinct_generators_with_ownership"] == 3

    assert alpha["reporting_utility_count"] == 2


def test_flags_incomplete_generator_shares(source_tables):
    ownership, utilities = source_tables

    result = build_ownership_evidence(
        ownership, utilities
    )

    alpha = get_owner(result, "100")
    beta = get_owner(result, "200")
    gamma = get_owner(result, "300")
    delta = get_owner(result, "400")

    # Alpha and Beta jointly own generator 10/G1.
    # Their reported shares total 1.0.
    assert alpha["generator_share_exception_count"] == 0
    assert beta["generator_share_exception_count"] == 0

    # Gamma's generator has only 0.9 reported.
    assert gamma["generator_share_exception_count"] == 1

    # Delta has a missing ownership share.
    assert delta["generator_share_exception_count"] == 1
    assert delta["missing_share_rows"] == 1


def test_flags_out_of_range_share(source_tables):
    ownership, utilities = source_tables

    ownership.loc[4, "Percent Owned"] = "1.2"

    result = build_ownership_evidence(
        ownership, utilities
    )

    gamma = get_owner(result, "300")

    assert gamma["invalid_share_rows"] == 1
    assert gamma["generator_share_exception_count"] == 1


def test_tracks_owner_name_variants(source_tables):
    ownership, utilities = source_tables

    ownership.loc[2, "Owner Name"] = " Alpha Energy "
    ownership.loc[3, "Owner Name"] = "Alpha Energy LLC"

    result = build_ownership_evidence(
        ownership, utilities
    )

    alpha = get_owner(result, "100")

    assert alpha["owner_name_variants"] == 2


def test_input_dataframes_are_not_modified(source_tables):
    ownership, utilities = source_tables

    original_ownership = ownership.copy(deep=True)
    original_utilities = utilities.copy(deep=True)

    build_ownership_evidence(ownership, utilities)

    pd.testing.assert_frame_equal(
        ownership, original_ownership
    )

    pd.testing.assert_frame_equal(
        utilities, original_utilities
    )


@pytest.mark.parametrize(
    "table, column",
    [
        ("ownership", "Percent Owned"),
        ("utilities", "Utility Name"),
    ],
)
def test_missing_columns_raise_error(
    source_tables, table, column
):
    ownership, utilities = source_tables

    if table == "ownership":
        ownership = ownership.drop(columns=[column])
    else:
        utilities = utilities.drop(columns=[column])

    with pytest.raises(ValueError, match="Missing"):
        build_ownership_evidence(ownership, utilities)


@pytest.mark.parametrize(
    "column",
    ["Ownership ID", "Plant Code", "Generator ID"],
)
def test_missing_ownership_identifiers_raise_error(
    source_tables, column
):
    ownership, utilities = source_tables

    ownership.loc[0, column] = None

    with pytest.raises(
        ValueError,
        match="Missing ownership/plant/generator identifier",
    ):
        build_ownership_evidence(ownership, utilities)


def test_duplicate_master_ids_raise_error(source_tables):
    ownership, utilities = source_tables

    utilities = pd.concat(
        [utilities, utilities.iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(
        ValueError,
        match="Duplicate Utility IDs",
    ):
        build_ownership_evidence(ownership, utilities)
