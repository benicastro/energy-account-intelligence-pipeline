"""Tests for utility-to-plant association logic."""

import pandas as pd
import pytest

from energy_intel.association import add_plant_counts


@pytest.fixture
def sample_data():
    """Create fictional utility and plant records."""

    accounts = pd.DataFrame({
        "account_id": [" 100 ", "200", "300", None],
        "account_name": [
            "Northwind Energy",
            "Example Power",
            "Sample Utilities",
            "Unknown Account",
        ],
        "associated_plant_count": pd.array(
            [pd.NA] * 4,
            dtype="Int64",
        ),
    })

    plants = pd.DataFrame({
        "Utility ID": [
            "100",
            "100",
            "100",
            "100",
            "200",
            None,
            " 100 ",
            "300",
            "",
            "200",
        ],
        "Plant Code": [
            "P-01",
            "P-01",   # Repeated plant
            "P-02",
            None,     # Missing plant code
            "P-99",
            "P-80",   # Missing utility ID
            " P-02 ", # Whitespace variation
            "",       # Blank plant code
            "P-80",   # Blank utility ID
            " P-99 ", # Repeated plant
        ],
    })

    return accounts, plants


def test_counts_distinct_plants(sample_data):
    accounts, plants = sample_data

    result = add_plant_counts(accounts, plants)

    # Utility 100 has two distinct plants.
    assert result.loc[0, "associated_plant_count"] == 2

    # Utility 200 has one distinct plant.
    assert result.loc[1, "associated_plant_count"] == 1


def test_missing_plant_identifiers_are_excluded(sample_data):
    accounts, plants = sample_data

    result = add_plant_counts(accounts, plants)

    # Utility 300 only has a blank plant code.
    assert result.loc[2, "associated_plant_count"] == 0


def test_missing_account_id_remains_missing(sample_data):
    accounts, plants = sample_data

    result = add_plant_counts(accounts, plants)

    # Do not invent associations for an unidentified account.
    assert pd.isna(
        result.loc[3, "associated_plant_count"]
    )


def test_original_data_is_not_modified(sample_data):
    accounts, plants = sample_data

    original_accounts = accounts.copy(deep=True)
    original_plants = plants.copy(deep=True)

    add_plant_counts(accounts, plants)

    pd.testing.assert_frame_equal(
        accounts, original_accounts
    )
    pd.testing.assert_frame_equal(
        plants, original_plants
    )


def test_missing_account_columns(sample_data):
    accounts, plants = sample_data

    invalid_accounts = accounts.drop(
        columns=["account_id"]
    )

    with pytest.raises(
        ValueError,
        match="Missing required account columns",
    ):
        add_plant_counts(invalid_accounts, plants)


def test_missing_plant_columns(sample_data):
    accounts, plants = sample_data

    invalid_plants = plants.drop(
        columns=["Plant Code"]
    )

    with pytest.raises(
        ValueError,
        match="Missing required plant columns",
    ):
        add_plant_counts(accounts, invalid_plants)
