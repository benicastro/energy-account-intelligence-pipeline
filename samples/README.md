# Public Account Intelligence Sample

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
