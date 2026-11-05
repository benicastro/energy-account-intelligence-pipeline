"""Tests for account data-quality checks."""

import pandas as pd
import pytest

from energy_intel.quality import flag_account_quality


@pytest.fixture
def sample_accounts():
    """Create fictional accounts with deliberate quality issues."""

    return pd.DataFrame({
        "account_id": [
            " 001 ",
            "001",
            "002",
            None,
            " ",
            "003",
        ],
        "account_name": [
            "Northwind Energy",
            "Northwind East",
            " ",
            "Unidentified Utility",
            "Blank Identifier Co",
            "Healthy Power",
        ],
        "state": [
            "NY",
            "NY",
            "CA",
            None,
            "TX",
            " WA ",
        ],
    })


def test_duplicate_account_ids(sample_accounts):
    result = flag_account_quality(sample_accounts)

    # Whitespace variations of 001 are duplicates.
    assert result["duplicate_account_id"].tolist() == [
        True,
        True,
        False,
        False,
        False,
        False,
    ]


def test_missing_fields(sample_accounts):
    result = flag_account_quality(sample_accounts)

    # Missing and blank identifiers are flagged.
    assert result.loc[3, "missing_account_id"]
    assert result.loc[4, "missing_account_id"]

    # Blank organization names are flagged.
    assert result.loc[2, "missing_account_name"]

    # Missing states are flagged.
    assert result.loc[3, "missing_state"]

    # Missing IDs are not treated as duplicate IDs.
    assert not result.loc[3, "duplicate_account_id"]
    assert not result.loc[4, "duplicate_account_id"]


def test_quality_issue_counts(sample_accounts):
    result = flag_account_quality(sample_accounts)

    assert result["quality_issue_count"].tolist() == [
        1,
        1,
        1,
        2,
        1,
        0,
    ]


def test_quality_status(sample_accounts):
    result = flag_account_quality(sample_accounts)

    assert (
        result["quality_status"].tolist()
        == ["review_required"] * 5 + ["no_basic_flags"]
    )

    # Passing these checks is not full CRM verification.
    assert result.loc[5, "quality_status"] == "no_basic_flags"


def test_original_data_is_not_modified(sample_accounts):
    original = sample_accounts.copy(deep=True)

    flag_account_quality(sample_accounts)

    pd.testing.assert_frame_equal(
        sample_accounts,
        original,
    )


@pytest.mark.parametrize(
    "missing_column",
    ["account_id", "account_name", "state"],
)
def test_missing_required_columns(
    sample_accounts,
    missing_column,
):
    incomplete = sample_accounts.drop(
        columns=[missing_column]
    )

    with pytest.raises(
        ValueError,
        match="Missing required columns",
    ):
        flag_account_quality(incomplete)
