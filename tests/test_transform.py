"""Tests for EIA utility data transformations."""

import pandas as pd
import pytest

from energy_intel.schema import ACCOUNT_COLUMNS
from energy_intel.transform import transform_utilities


@pytest.fixture
def sample_utilities():
    """Create fictional utility records for testing."""

    return pd.DataFrame({
        "Utility ID": [" 0007 ", "8"],
        "Utility Name": [
            "  Northwind   Energy LLC  ",
            "   ",
        ],
        "Entity Type": [" Q ", "M"],
        "City": [" Albany ", None],
        "State": [" NY ", "CA"],
        "Zip": [" 00501 ", "90001"],
        "Owner of Plants Reported on Form?": [
            " Y ", None
        ],
        "Operator of Plants Reported on Form?": [
            "", " Y "
        ],
    })


def test_standardized_schema(sample_utilities):
    accounts = transform_utilities(sample_utilities)

    assert list(accounts.columns) == ACCOUNT_COLUMNS
    assert len(accounts) == 2

    first = accounts.iloc[0]

    assert first["account_id"] == "0007"
    assert first["account_name"] == "Northwind Energy LLC"
    assert first["entity_type_code"] == "Q"
    assert first["city"] == "Albany"
    assert first["state"] == "NY"
    assert first["postal_code"] == "00501"
    assert first["reports_plant_ownership"] == "Y"

    assert first["source_year"] == 2025
    assert first["source_name"] == "EIA-860"


def test_missing_values_are_preserved(sample_utilities):
    accounts = transform_utilities(sample_utilities)

    second = accounts.iloc[1]

    # Blank company names become missing values.
    assert pd.isna(second["account_name"])

    # Missing address information remains missing.
    assert pd.isna(second["city"])

    # Missing ownership information is not assumed "N".
    assert pd.isna(second["reports_plant_ownership"])

    # Plant counts have not been calculated yet.
    assert accounts["associated_plant_count"].isna().all()


def test_missing_required_columns(sample_utilities):
    incomplete = sample_utilities.drop(
        columns=["Utility ID"]
    )

    with pytest.raises(
        ValueError,
        match="Missing required columns"
    ):
        transform_utilities(incomplete)


def test_source_data_is_not_modified(sample_utilities):
    original = sample_utilities.copy(deep=True)

    transform_utilities(sample_utilities)

    pd.testing.assert_frame_equal(
        sample_utilities,
        original
    )
