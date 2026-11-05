"""Tests for preliminary EIA-860 ICP classification."""

import pandas as pd
import pytest

from energy_intel.classification import classify_accounts


@pytest.mark.parametrize(
    "code, plant_count, quality_status, expected_tier",
    [
        # Primary ICP: energy industry categories
        ("Q", 1, "no_basic_flags",
         "Tier 1 - Preliminary"),

        ("I", 5, "no_basic_flags",
         "Tier 1 - Preliminary"),

        # Code normalization should handle whitespace/case
        (" m ", 2, "no_basic_flags",
         "Tier 1 - Preliminary"),

        # Secondary ICP: industrial and commercial
        ("IND", 1, "no_basic_flags",
         "Tier 2 - Preliminary"),

        ("COM", 3, "no_basic_flags",
         "Tier 2 - Preliminary"),

        # Unknown entity codes require research
        ("UNKNOWN", 2, "no_basic_flags",
         "Needs Research"),

        # No matching plant associations
        ("Q", 0, "no_basic_flags",
         "Needs Research"),

        # Existing quality flags override preliminary tiers
        ("Q", 4, "review_required",
         "Needs Research"),

        # Missing evidence cannot support qualification
        ("S", None, "no_basic_flags",
         "Needs Research"),
    ],
)
def test_icp_tier_assignment(
    code,
    plant_count,
    quality_status,
    expected_tier,
):
    accounts = pd.DataFrame({
        "entity_type_code": [code],
        "associated_plant_count": [plant_count],
        "quality_status": [quality_status],
    })

    result = classify_accounts(accounts)

    assert result.loc[0, "icp_tier"] == expected_tier


def test_classification_metadata():
    accounts = pd.DataFrame({
        "entity_type_code": ["Q", "IND", "UNKNOWN"],
        "associated_plant_count": [2, 1, 3],
        "quality_status": ["no_basic_flags"] * 3,
    })

    result = classify_accounts(accounts)

    assert (
        result.loc[0, "entity_type_description"]
        == "Independent Power Producer"
    )

    assert (
        result.loc[1, "entity_type_description"]
        == "Industrial"
    )

    assert (
        result.loc[2, "entity_type_description"]
        == "Unknown or missing entity type"
    )

    assert result["icp_rationale"].notna().all()
    assert (result["icp_rule_version"] == "1.0").all()
    assert (result["icp_source_year"] == 2025).all()


def test_original_dataframe_unchanged():
    accounts = pd.DataFrame({
        "entity_type_code": ["Q", "COM"],
        "associated_plant_count": [5, 2],
        "quality_status": [
            "no_basic_flags",
            "review_required",
        ],
    })

    original = accounts.copy(deep=True)

    classify_accounts(accounts)

    pd.testing.assert_frame_equal(accounts, original)


@pytest.mark.parametrize(
    "missing_column",
    [
        "entity_type_code",
        "associated_plant_count",
        "quality_status",
    ],
)
def test_missing_required_columns(missing_column):
    accounts = pd.DataFrame({
        "entity_type_code": ["Q"],
        "associated_plant_count": [1],
        "quality_status": ["no_basic_flags"],
    })

    incomplete = accounts.drop(columns=[missing_column])

    with pytest.raises(
        ValueError,
        match="Missing required columns",
    ):
        classify_accounts(incomplete)
