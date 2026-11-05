"""Generate a reproducible, public EIA account sample."""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

SOURCE = (
    ROOT
    / "data/processed/eia860_2025_accounts_with_ownership.csv"
)

SAMPLE_DIR = ROOT / "samples"

OUTPUT = SAMPLE_DIR / "eia860_2025_account_sample.csv"

DOCUMENTATION = SAMPLE_DIR / "README.md"


SAMPLE_COLUMNS = [
    "account_id",
    "account_name",
    "city",
    "state",
    "entity_type_description",
    "associated_plant_count",
    "icp_tier",
    "quality_status",
    "ownership_evidence_status",
    "distinct_plants_with_ownership",
    "distinct_generators_with_ownership",
    "generator_share_exception_count",
]


def generate_sample():
    if not SOURCE.is_file():
        raise FileNotFoundError(
            f"Missing linked account dataset: {SOURCE}\n"
            "Run energy_intel.ownership_linkage first."
        )

    accounts = pd.read_csv(
        SOURCE,
        dtype="string",
        keep_default_na=False,
    )

    missing = set(SAMPLE_COLUMNS) - set(accounts.columns)

    if missing:
        raise ValueError(
            f"Missing required sample columns: {sorted(missing)}"
        )

    matched = accounts["ownership_evidence_status"].eq(
        "source_reported_owner_match"
    )

    tier1 = accounts["icp_tier"].eq(
        "Tier 1 - Preliminary"
    )

    groups = [
        ("Tier 1 - Ownership Match", tier1 & matched),
        ("Tier 1 - No Ownership Match", tier1 & ~matched),
        (
            "Tier 2 - Preliminary",
            accounts["icp_tier"].eq("Tier 2 - Preliminary"),
        ),
        (
            "Needs Research",
            accounts["icp_tier"].eq("Needs Research"),
        ),
    ]

    selected = []

    for label, condition in groups:
        candidates = (
            accounts.loc[condition]
            .sort_values("account_id")
            .head(6)
            .copy()
        )

        if len(candidates) < 6:
            raise ValueError(
                f"Not enough records for {label}: "
                f"found {len(candidates)}, need 6"
            )

        candidates["sample_group"] = label

        selected.append(candidates)

    sample = pd.concat(
        selected,
        ignore_index=True,
    )

    sample = sample[
        ["sample_group"] + SAMPLE_COLUMNS
    ]

    assert len(sample) == 24
    assert sample["account_id"].is_unique
    assert sample["sample_group"].value_counts().eq(6).all()

    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    sample.to_csv(
        OUTPUT,
        index=False,
        encoding="utf-8",
    )

    documentation = """# Public Account Intelligence Sample

This directory contains a small, reproducible sample
generated from the public 2025 EIA-860 dataset.

## Contents

- `eia860_2025_account_sample.csv`: 24 organization
  records illustrating account segmentation and
  generator-ownership evidence.

## Selection methodology

The sample intentionally includes six records from
each of four groups:

1. Tier 1 accounts with source-reported owner matches.
2. Tier 1 accounts without matched ownership records.
3. Tier 2 preliminary accounts.
4. Accounts requiring additional research.

Within each group, records are selected by sorting
their EIA account identifiers as strings and taking
the first six.

**This is a demonstration sample, not a random or
statistically representative sample.**

## Interpretation

- `associated_plant_count` counts distinct plants
  associated with the EIA reporting utility.
- `distinct_plants_with_ownership` counts distinct
  plants found in generator-level ownership records
  attributed to the matching owner identifier.
- A missing ownership count means no matching
  record was found in the ownership table; it
  must not be interpreted as zero owned plants.
- `generator_share_exception_count` flags generator
  groups with incomplete or unusual reported
  ownership shares.
- ICP tiers reflect project-defined screening
  rules, not official EIA classifications or
  verified sales qualifications.

## Source

U.S. Energy Information Administration (EIA),
2025 Form EIA-860 annual data.

https://www.eia.gov/electricity/data/eia860/

## Reproduction

After generating the main account and ownership
exports, run:

```powershell
$env:PYTHONPATH = "src"
python -m energy_intel.export_public_sample
```

No confidential client data, private contact records,
or personal enrichment data are included.
"""

    DOCUMENTATION.write_text(
        documentation,
        encoding="utf-8",
    )

    print("\nPUBLIC ACCOUNT SAMPLE GENERATED")
    print("=" * 60)

    print(f"Records: {len(sample)}")
    print(f"Columns: {len(sample.columns)}")

    print("\nSample groups:")
    print(sample["sample_group"].value_counts().to_string())

    print("\nFiles:")
    print(f"  CSV: {OUTPUT}")
    print(f"  Documentation: {DOCUMENTATION}")

    print("\nFirst five sample records:")
    print(
        sample[
            [
                "account_id",
                "account_name",
                "icp_tier",
                "ownership_evidence_status",
            ]
        ]
        .head()
        .to_string(index=False)
    )


if __name__ == "__main__":
    generate_sample()
