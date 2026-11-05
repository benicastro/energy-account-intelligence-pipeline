"""Tests for the public EIA account sample generator."""

import pandas as pd
import pytest

from energy_intel import export_public_sample


@pytest.fixture
def sample_setup(tmp_path, monkeypatch):
    """Prepare fictional linked accounts and temporary outputs."""

    source = tmp_path / "processed" / "accounts.csv"
    sample_dir = tmp_path / "samples"
    output = sample_dir / "account_sample.csv"
    documentation = sample_dir / "README.md"

    monkeypatch.setattr(
        export_public_sample, "SOURCE", source
    )
    monkeypatch.setattr(
        export_public_sample, "SAMPLE_DIR", sample_dir
    )
    monkeypatch.setattr(
        export_public_sample, "OUTPUT", output
    )
    monkeypatch.setattr(
        export_public_sample, "DOCUMENTATION", documentation
    )

    rows = []

    groups = [
        (
            "Tier 1 - Preliminary",
            "source_reported_owner_match",
        ),
        (
            "Tier 1 - Preliminary",
            "no_matched_record_in_ownership_table",
        ),
        (
            "Tier 2 - Preliminary",
            "no_matched_record_in_ownership_table",
        ),
        (
            "Needs Research",
            "no_matched_record_in_ownership_table",
        ),
    ]

    # Seven records per group: the generator must select six.
    for group_number, (tier, status) in enumerate(
        groups, start=1
    ):
        for number in range(7):
            matched = (
                status == "source_reported_owner_match"
            )

            rows.append({
                "account_id": f"{group_number}{number:04d}",
                "account_name": (
                    f"Fictional Company {group_number}-{number}"
                ),
                "city": "Sample City",
                "state": "TX",
                "entity_type_description": (
                    "Independent Power Producer"
                ),
                "associated_plant_count": "2",
                "icp_tier": tier,
                "quality_status": "no_basic_flags",
                "ownership_evidence_status": status,
                "distinct_plants_with_ownership": (
                    "2" if matched else ""
                ),
                "distinct_generators_with_ownership": (
                    "3" if matched else ""
                ),
                "generator_share_exception_count": (
                    "0" if matched else ""
                ),
            })

    source.parent.mkdir(parents=True, exist_ok=True)

    # Intentionally reverse the order to test deterministic
    # selection by account_id.
    pd.DataFrame(rows[::-1]).to_csv(
        source, index=False
    )

    return {
        "source": source,
        "output": output,
        "documentation": documentation,
    }


def test_sample_has_correct_distribution(sample_setup):
    export_public_sample.generate_sample()

    output = pd.read_csv(
        sample_setup["output"],
        dtype="string",
        keep_default_na=False,
    )

    assert len(output) == 24
    assert len(output.columns) == 13
    assert output["account_id"].is_unique

    counts = output["sample_group"].value_counts()

    assert len(counts) == 4
    assert counts.eq(6).all()

    assert sample_setup["documentation"].is_file()


def test_sample_is_reproducible(sample_setup):
    export_public_sample.generate_sample()

    first_output = sample_setup["output"].read_bytes()

    export_public_sample.generate_sample()

    second_output = sample_setup["output"].read_bytes()

    assert first_output == second_output


def test_missing_ownership_is_not_zero(sample_setup):
    export_public_sample.generate_sample()

    output = pd.read_csv(
        sample_setup["output"],
        dtype="string",
        keep_default_na=False,
    )

    unmatched = output.loc[
        output["ownership_evidence_status"]
        == "no_matched_record_in_ownership_table"
    ]

    assert unmatched[
        "distinct_plants_with_ownership"
    ].eq("").all()

    assert unmatched[
        "distinct_generators_with_ownership"
    ].eq("").all()


def test_missing_required_column_raises_error(sample_setup):
    source = sample_setup["source"]

    accounts = pd.read_csv(source, dtype="string")

    accounts = accounts.drop(
        columns=["ownership_evidence_status"]
    )

    accounts.to_csv(source, index=False)

    with pytest.raises(
        ValueError,
        match="Missing required sample columns",
    ):
        export_public_sample.generate_sample()


def test_insufficient_category_raises_error(sample_setup):
    source = sample_setup["source"]

    accounts = pd.read_csv(
        source,
        dtype="string",
        keep_default_na=False,
    )

    # Leave only five Needs Research records.
    needs_research = accounts[
        accounts["icp_tier"] == "Needs Research"
    ]

    accounts = accounts.drop(
        needs_research.index[:2]
    )

    accounts.to_csv(source, index=False)

    with pytest.raises(
        ValueError,
        match="Not enough records",
    ):
        export_public_sample.generate_sample()


def test_missing_source_raises_error(sample_setup):
    sample_setup["source"].unlink()

    with pytest.raises(
        FileNotFoundError,
        match="Missing linked account dataset",
    ):
        export_public_sample.generate_sample()
