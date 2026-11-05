"""Integration tests for the ownership evidence exporter."""

import json

import pandas as pd
import pytest

from energy_intel import export_ownership


@pytest.fixture
def exported_ownership(tmp_path, monkeypatch):
    """Run the exporter with small, fictional source tables."""

    ownership = pd.DataFrame({
        "Ownership ID": [
            "100", "200", "100", "300", "300"
        ],
        "Owner Name": [
            "Alpha Energy",
            "Beta Power",
            "Alpha Energy",
            "Gamma Generation",
            "Gamma Generation",
        ],
        "Utility ID": [
            "900", "900", "900", "900", "900"
        ],
        "Plant Code": [
            "10", "10", "20", "30", "40"
        ],
        "Generator ID": [
            "G1", "G1", "G1", "G2", "G1"
        ],
        "Percent Owned": [
            "0.6", "0.4", "1.0", "0.9", None
        ],
    })

    utilities = pd.DataFrame({
        "Utility ID": ["100", "200", "900"],
        "Utility Name": [
            "Alpha Energy",
            "Beta Power",
            "Reporting Utility",
        ],
    })

    original_ownership = ownership.copy(deep=True)
    original_utilities = utilities.copy(deep=True)

    def fake_loader(dataset):
        if dataset == "ownership":
            return ownership.copy(deep=True)

        if dataset == "utility":
            return utilities.copy(deep=True)

        raise ValueError(f"Unexpected dataset: {dataset}")

    csv_path = tmp_path / "processed" / "ownership.csv"
    report_path = tmp_path / "reports" / "summary.json"

    monkeypatch.setattr(
        export_ownership,
        "load_dataset",
        fake_loader,
    )

    monkeypatch.setattr(
        export_ownership,
        "OUTPUT_CSV",
        csv_path,
    )

    monkeypatch.setattr(
        export_ownership,
        "OUTPUT_REPORT",
        report_path,
    )

    evidence, summary = (
        export_ownership.export_ownership_evidence()
    )

    return {
        "evidence": evidence,
        "summary": summary,
        "csv_path": csv_path,
        "report_path": report_path,
        "ownership": ownership,
        "utilities": utilities,
        "original_ownership": original_ownership,
        "original_utilities": original_utilities,
    }


def test_export_files_and_owner_matching(exported_ownership):
    result = exported_ownership

    assert result["csv_path"].is_file()
    assert result["report_path"].is_file()

    exported = pd.read_csv(
        result["csv_path"],
        dtype="string",
        keep_default_na=False,
    )

    assert len(exported) == 3
    assert exported["owner_id"].is_unique

    matched = exported.loc[
        exported["matched_to_account_master"] == "True"
    ]

    unmatched = exported.loc[
        exported["matched_to_account_master"] == "False"
    ]

    assert set(matched["owner_id"]) == {"100", "200"}
    assert set(unmatched["owner_id"]) == {"300"}

    # Reporting utility 900 must not become an owner.
    assert "900" not in set(exported["owner_id"])

    assert (
        exported.loc[
            exported["owner_id"] == "100",
            "matched_account_name",
        ].iloc[0]
        == "Alpha Energy"
    )


def test_ownership_summary_reconciles(exported_ownership):
    result = exported_ownership
    summary = result["summary"]

    records = summary["records"]

    assert records["ownership_source_rows"] == 5
    assert records["distinct_owner_entities"] == 3
    assert records["matched_owner_accounts"] == 2
    assert records["unmatched_owner_entities"] == 1

    quality = summary["evidence_quality"]

    # Gamma has two generators with incomplete shares.
    assert quality["owners_with_share_exceptions"] == 1
    assert quality["owners_with_missing_shares"] == 1
    assert quality["owners_with_invalid_shares"] == 0

    evidence = result["evidence"].set_index("owner_id")

    assert evidence.loc[
        "100", "distinct_plants_with_ownership"
    ] == 2

    assert evidence.loc[
        "100", "distinct_generators_with_ownership"
    ] == 2

    assert evidence.loc[
        "300", "generator_share_exception_count"
    ] == 2

    with result["report_path"].open(
        encoding="utf-8"
    ) as file:
        saved_summary = json.load(file)

    assert saved_summary == summary


def test_export_preserves_inputs_and_metadata(
    exported_ownership,
):
    result = exported_ownership

    pd.testing.assert_frame_equal(
        result["ownership"],
        result["original_ownership"],
    )

    pd.testing.assert_frame_equal(
        result["utilities"],
        result["original_utilities"],
    )

    evidence = result["evidence"]

    assert (evidence["source_name"] == "EIA-860").all()
    assert (evidence["source_year"] == 2025).all()
    assert (evidence["source_table"] == "Ownership").all()

    assert evidence["evidence_status"].eq(
        "Source-reported generator ownership interest"
    ).all()
