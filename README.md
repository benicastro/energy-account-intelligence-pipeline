# Energy Account Intelligence Pipeline


[![Python Tests](https://github.com/benicastro/energy-account-intelligence-pipeline/actions/workflows/tests.yml/badge.svg?branch=master)](https://github.com/benicastro/energy-account-intelligence-pipeline/actions/workflows/tests.yml)


**A reproducible Python portfolio project for public energy-sector data processing, account intelligence, data-quality auditing, preliminary ICP segmentation, and generator-ownership relationship analysis.**

This independent project processes the **2025 U.S. Energy Information Administration (EIA) Form EIA-860** data. It demonstrates how to turn raw public records into structured, auditable account datasets, link related records using source identifiers, identify data-quality exceptions, and preserve evidence for further research.

> **Scope:** This is a technical and analytical portfolio project, **not** a verified prospect list or a production-ready CRM import. The project uses public EIA data and fictional test fixtures; it does not contain confidential client data.

## What the project does

1. **Ingest:** Read EIA utility, plant, and generator-ownership Excel workbooks directly from the annual ZIP archive.
2. **Standardize:** Map source fields to a documented account schema, normalize company-name whitespace, and retain source metadata.
3. **Associate:** Count distinct plants reported against each EIA Utility ID without inflating counts from repeated records.
4. **Audit:** Flag missing identifiers, names, and states, as well as duplicate nonblank account IDs; preserve records for review.
5. **Classify:** Apply transparent, project-defined preliminary ideal customer profile (ICP) rules and export a rationale for each account.
6. **Analyze ownership:** Attribute generator-level ownership records to their **Ownership ID**, not automatically to the reporting utility; calculate distinct plant/generator counts and flag anomalous ownership shares.
7. **Resolve relationships:** Match owner IDs to account IDs, retain all original accounts, and export unmatched owner entities separately for additional research.
8. **Validate and export:** Write CSV evidence datasets and JSON audit summaries, run reconciliation checks, and test the components and workflows with pytest.

## Results using 2025 EIA-860 data

### Account intelligence

| Measure | Result |
|---|---:|
| Utility source rows | 6,946 |
| Plant source rows | 17,349 |
| Standardized account records | 6,946 |
| Accounts with at least one reported plant association | 6,944 |
| Records requiring basic quality review | 9 |
| Missing state flags | 9 |
| Missing account ID / name flags | 0 / 0 |
| Duplicate account ID flags | 0 |

**Preliminary ICP distribution** (project-defined screening, not sales qualification):

| Category | Accounts |
|---|---:|
| Tier 1 — Preliminary | 6,110 |
| Tier 2 — Preliminary | 825 |
| Needs Research | 11 |

The main account pipeline produces a **22-column review CSV**, including entity-type descriptions, preliminary ICP tiers, rationale, and rule-version metadata. A high preliminary tier is **not** evidence of verified ownership, geography fit, purchase intent, or an approved outreach contact.

### Generator ownership intelligence

| Measure | Result |
|---|---:|
| Source-reported ownership rows | 5,680 |
| Distinct owner IDs | 2,047 |
| Owners matched to the utility account master | 313 |
| Owners not matched to the utility account master | 1,734 |
| Accounts with no matching owner record in this table | 6,633 |
| Owners with generator-share exceptions | 4 |
| Owners with missing ownership shares | 1 |
| Owners with out-of-range ownership shares | 0 |

Ownership analysis is **a separate, linked evidence workflow**. It does not automatically alter the ICP tiers assigned by the account pipeline.

**Interpretation:** An owner match means there is a corresponding source-reported ownership identifier in the EIA table. An account without a match is marked `no_matched_record_in_ownership_table`; **it is not classified as owning zero plants**. Several owners may have interests in the same generator, and repeated generator IDs at different plants are treated as distinct units.

## Explore the public sample

A curated 24-record sample is available in the
[`samples/`](samples/) directory.

The sample demonstrates:

- Standardized energy-sector company records
- Preliminary ICP segmentation and classification
- Plant association counts
- Generator ownership evidence
- Distinctions between matched and unmatched ownership records
- Identification of records requiring further research

The sample contains six records from each of four
categories:

| Category | Records |
|---|---:|
| Tier 1 with ownership matches | 6 |
| Tier 1 without ownership matches | 6 |
| Tier 2 preliminary accounts | 6 |
| Needs Research | 6 |
| **Total** | **24** |

**Note:** This is an intentionally selected demonstration
sample, not a statistically representative sample.
Preliminary ICP classifications do not imply verified
sales qualification.

See the [sample methodology](samples/README.md)
for selection rules, field definitions, and limitations.

## Technology

- Python 3.12
- pandas and openpyxl for ingestion, transformations, and tabular audits
- Python `zipfile`, `pathlib`, and `json` for archive processing and reporting
- pytest for unit and integration tests
- CSV and JSON for reviewable downstream data and audit reports

## Data source and preparation

Download the **2025 EIA-860 annual ZIP** from the official [U.S. EIA Form EIA-860 data page](https://www.eia.gov/electricity/data/eia860/).

Save it at:

```text
data/raw/eia8602025.zip
```

The loader uses these workbooks and sheets from the archive:

| File in ZIP | Worksheet | Use |
|---|---|---|
| `1___Utility_Y2025.xlsx` | `Utility` | Account master |
| `2___Plant_Y2025.xlsx` | `Plant` | Plant associations |
| `4___Owner_Y2025.xlsx` | `Ownership` | Generator ownership evidence |
| `LayoutY2025.xlsx` | Data dictionary worksheets | Interpret fields and entity codes |

Workbook column names begin on **Excel row 2**, so the loader uses `header=1`. EIA `Entity Type` definitions are taken from the data dictionary in the source archive.

The source ZIP and generated full-size CSV datasets are intentionally excluded from Git through `.gitignore`. The code, tests, and aggregate JSON reports can be version-controlled without committing the large raw dataset.

## Run locally

The following examples use **Windows PowerShell** from the repository root.

### 1. Set up the project

```powershell
git clone https://github.com/benicastro/energy-account-intelligence-pipeline.git
cd energy-account-intelligence-pipeline
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
```

Download the EIA-860 archive and save it at `data/raw/eia8602025.zip` before running the data workflows.

### 2. Generate and validate account intelligence

```powershell
python -m energy_intel.pipeline
python -m energy_intel.validate_exports
```

Outputs:

```text
data/processed/eia860_2025_accounts_review.csv
reports/eia860_2025_quality_summary.json
```

### 3. Generate generator ownership evidence

```powershell
python -m energy_intel.export_ownership
```

Outputs:

```text
data/processed/eia860_2025_ownership_evidence.csv
reports/eia860_2025_ownership_summary.json
```

### 4. Link ownership evidence to accounts and reconcile

Run this **after** both the account and ownership exports have been generated:

```powershell
python -m energy_intel.ownership_linkage
python -m energy_intel.validate_ownership_linkage
```

Outputs:

```text
data/processed/eia860_2025_accounts_with_ownership.csv
data/processed/eia860_2025_unmatched_owners.csv
reports/eia860_2025_ownership_linkage_summary.json
```

### 5. Run tests

```powershell
python -m pytest -q
```

**Test coverage:** **72 passing automated tests** in the latest local development milestone, including source transformation, plant-association counting, data-quality flags, preliminary ICP classification, generator ownership aggregation, ownership exports, identifier-based linkage, and end-to-end integration testing with fictional data. The integration tests do not require the downloaded EIA ZIP. A GitHub Actions continuous-integration workflow has not yet been configured.

For macOS/Linux, activate the virtual environment with `source .venv/bin/activate` and set the Python import path with `export PYTHONPATH=src`.

## Repository layout

```text
src/energy_intel/
  __init__.py
  schema.py                     # Source field mappings and account schema
  loader.py                     # EIA workbooks read from ZIP archive
  normalization.py              # Company-name normalization
  transform.py                  # Standardized utility account records
  association.py                # Distinct reported plant associations
  quality.py                    # Basic data-quality flags
  classification.py             # Project-defined preliminary ICP tiers
  pipeline.py                   # Account CSV and JSON report generation
  validate_exports.py           # Account export reconciliation
  inspect_eia.py                # Source data exploration
  profile_accounts.py           # Account/entity distribution profiling
  inspect_ownership.py          # Ownership source exploration
  audit_ownership.py            # Ownership identifier/share checks
  ownership_evidence.py         # Generator ownership -> owner-level evidence
  export_ownership.py           # Ownership evidence CSV and JSON export
  ownership_linkage.py          # Match owner IDs to account IDs
  validate_ownership_linkage.py # Cross-export linkage reconciliation

tests/                           # pytest unit and integration tests
reports/                         # Aggregate, shareable JSON reports
data/raw/                        # Local EIA ZIP (Git-ignored)
data/processed/                  # Generated CSV files (Git-ignored)
```

## Methodology and safeguards

- **Identifiers over name guesses:** EIA account IDs and owner IDs are retained as strings. Ownership attribution uses `Ownership ID`; the `Utility ID` on an ownership row represents the reporting utility and is not automatically assumed to be the owner.
- **No inflated asset counts:** Distinct plants are counted by Plant Code, and distinct generators by the Plant Code + Generator ID combination.
- **Share anomalies are visible:** Missing, invalid, or inconsistent generator-level ownership-share totals are flagged rather than silently repaired. Percentages are *not* summed into a misleading company-wide ownership percentage.
- **Unmatched entities survive:** Owners absent from the utility master remain in a separate export for future research, rather than being dropped or matched by unverified company-name similarity.
- **Absence is not zero:** No owner-record match does not establish that an account owns no generation assets. Missing evidence is preserved as missing.
- **Explainable preliminary ICP rules:** Tier assignments are documented and reproduceable, but are not official EIA categories or verified sales qualifications. Ownership evidence does not currently change preliminary ICP tiers.
- **Reproducibility:** CSV/JSON outputs have reconciliation checks, and automated tests use fictional fixtures to cover edge cases without relying on private data or external services.

## Known limitations and roadmap

- The published ownership information is **source-reported generator-level evidence**, not independently verified beneficial ownership or a comprehensive record of all assets a company owns.
- Generator operational status is not yet incorporated into qualification; a reported ownership interest is not proof that an asset is currently operating.
- The ICP categories are deliberately broad and do not yet establish geography fit, business relevance, procurement authority, contact validity, or outreach suitability.
- The 1,734 unmatched owners require additional identity and company research before they can become usable accounts in a CRM workflow.
- The main account export and ownership exports are separate, with an explicit linkage step. Ownership results do not automatically re-score ICP tiers.
- Version-pinned dependencies, automated CI, source refresh/scheduling, and a compact published sample dataset are planned improvements.
- Next steps include a small reproducible public sample, stronger ownership/status validation, more targeted ICP filters, and CI checks.

## Author

**Benedict Z. Castro** — Python automation, B2B account intelligence, data quality, and software engineering.

- [Professional portfolio](https://benicastro.github.io/benedict-portfolio/)
- [GitHub profile](https://github.com/benicastro)

*Independent project using public data. No confidential client records or proprietary source code are included.*
