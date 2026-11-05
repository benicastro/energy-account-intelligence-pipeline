"""End-to-end integration test using fictional data."""

import json

import pandas as pd

from energy_intel import pipeline, validate_exports


def test_complete_pipeline(tmp_path, monkeypatch):
    """Verify ingestion, transformation, ICP, and exports."""

    utilities = pd.DataFrame({
        "Utility ID": ["100", "200", "300", "400"],
        "Utility Name": [
            "  Northwind   Energy LLC ",
            "Sample Industrial Co",
            "Example Municipal Power",
            "Test Federal Utility",
        ],
        "Entity Type": ["Q", "IND", "M", "F"],
        "City": ["Albany", "Austin", "Seattle", "Denver"],
        "State": ["NY", "TX", "WA", None],
        "Zip": ["12201", "78701", "98101", "80201"],
        "Owner of Plants Reported on Form?": [
            "Y", "Y", None, "Y"
        ],
        "Operator of Plants Reported on Form?": [
            "Y", None, None, "Y"
        ],
    })

    plants = pd.DataFrame({
        "Utility ID": ["100", "100", "100", "200", "400"],
        "Plant Code": [
            "P-01",
            "P-01",  # Repeated plant association
            "P-02",
            "P-03",
            "P-04",
        ],
    })

    def fake_loader(dataset):
        if dataset == "utility":
            return utilities.copy(deep=True)
        if dataset == "plant":
            return plants.copy(deep=True)
        raise ValueError(f"Unexpected dataset: {dataset}")

    csv_path = tmp_path / "accounts.csv"
    report_path = tmp_path / "summary.json"

    # Replace external data loading and output paths.
    monkeypatch.setattr(
        pipeline, "load_dataset", fake_loader
    )
    monkeypatch.setattr(
        pipeline, "OUTPUT_CSV", csv_path
    )
    monkeypatch.setattr(
        pipeline, "OUTPUT_REPORT", report_path
    )

    # Execute the complete pipeline.
    accounts, summary = pipeline.run_pipeline()

    # Verify that both files were generated.
    assert csv_path.is_file()
    assert report_path.is_file()

    # Check account processing and plant associations.
    assert len(accounts) == 4

    assert accounts.loc[
        accounts["account_id"] == "100",
        "associated_plant_count"
    ].iloc[0] == 2

    assert accounts.loc[
        accounts["account_id"] == "100",
        "account_name"
    ].iloc[0] == "Northwind Energy LLC"

    # Check the complete classification workflow.
    tiers = accounts.set_index("account_id")["icp_tier"]

    assert tiers["100"] == "Tier 1 - Preliminary"
    assert tiers["200"] == "Tier 2 - Preliminary"
    assert tiers["300"] == "Needs Research"
    assert tiers["400"] == "Needs Research"

    # Missing state triggers a quality-review flag.
    assert summary["data_quality"][
        "records_requiring_review"
    ] == 1

    assert summary["records"][
        "accounts_with_associated_plants"
    ] == 3

    assert summary["icp_classification"][
        "preliminary_tier_counts"
    ] == {
        "Needs Research": 2,
        "Tier 1 - Preliminary": 1,
        "Tier 2 - Preliminary": 1,
    }

    # Verify the JSON was actually written.
    with report_path.open(encoding="utf-8") as file:
        saved_report = json.load(file)

    assert saved_report == summary

    # Run the existing independent export validator.
    monkeypatch.setattr(
        validate_exports, "CSV_PATH", csv_path
    )
    monkeypatch.setattr(
        validate_exports, "REPORT_PATH", report_path
    )

    validate_exports.validate_exports()
