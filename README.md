# Energy Account Intelligence Pipeline

**A reproducible Python project for public energy-sector data processing, account-level analysis, data-quality review, and preliminary ICP segmentation.**

This independent portfolio project uses the **2025 U.S. Energy Information Administration (EIA) Form EIA-860** dataset to demonstrate how raw public-sector records can be turned into consistent, auditable account data. It combines Python ingestion, pandas transformations, distinct plant associations, quality checks, and documented targeting rules.

> **Scope:** This is a technical demonstration—not a verified lead list or a production-ready CRM import. The source is public government data; no private client records are included.

## What the project does

1. **Ingest:** Read selected Excel workbooks directly from the original EIA-860 ZIP archive.
2. **Standardize:** Map EIA utility fields to a consistent account schema, normalize company-name whitespace, and retain source metadata.
3. **Associate:** Count distinct reported plants linked to each EIA Utility ID.
4. **Audit:** Flag missing account IDs, names, and states, and repeated nonblank account IDs without deleting records.
5. **Export:** Write an account review CSV and a JSON quality summary, then reconcile the two outputs.
6. **Classify (separate exploratory step):** Apply transparent preliminary ICP rules based on EIA entity categories, associated plant counts, and basic quality status.

## Results from the 2025 EIA-860 data

The following figures are from the project's generated quality report, not estimates:

| Measure | Result |
|---|---:|
| Utility source records | 6,946 |
| Plant source records | 17,349 |
| Standardized account records | 6,946 |
| Accounts with at least one associated plant | 6,944 |
| Account records requiring basic quality review | 9 |
| Missing state flags | 9 |
| Missing account ID flags | 0 |
| Missing account name flags | 0 |
| Duplicate account ID flags | 0 |

The standalone, rule-based **preliminary ICP classifier** produced the following exploratory segmentation:

| Classification | Accounts |
|---|---:|
| Tier 1 — Preliminary | 6,110 |
| Tier 2 — Preliminary | 825 |
| Needs Research | 11 |

**Important:** ICP classification is implemented in `classification.py` but is **not yet integrated into the main CSV export**. These preliminary categories are *not* verified sales-qualified accounts. Plant associations do not prove plant ownership, and an account with no basic quality flags has not been commercially verified.

## Technology

- Python 3.12 (developed and tested locally)
- pandas and openpyxl for tabular ingestion and transformation
- `zipfile` for direct ZIP archive access
- pytest for automated testing
- CSV and JSON outputs for downstream review and auditability

## Source data

Download the **2025 EIA-860** annual data ZIP from the official [EIA Form EIA-860 data page](https://www.eia.gov/electricity/data/eia860/).

Save the downloaded archive as:

```text
data/raw/eia8602025.zip
```

The loader currently expects these files inside that archive:

- `1___Utility_Y2025.xlsx` — `Utility` worksheet
- `2___Plant_Y2025.xlsx` — `Plant` worksheet
- `4___Owner_Y2025.xlsx` — `Ownership` worksheet (loader supported; ownership analysis is not yet integrated)

The EIA workbooks have column headings on **Excel row 2**; the loader uses `header=1` in pandas. The large downloaded ZIP and generated full account CSV are intentionally excluded from Git to keep the repository focused on reproducible code and safe-to-share reports.

## Run locally

Clone the repository and open a terminal in the project root:

```powershell
git clone https://github.com/benicastro/energy-account-intelligence-pipeline.git
cd energy-account-intelligence-pipeline
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Place `eia8602025.zip` in `data/raw/` as described above, then execute:

```powershell
$env:PYTHONPATH = "src"
python -m energy_intel.pipeline
python -m energy_intel.validate_exports
```

The main pipeline produces:

```text
data/processed/eia860_2025_accounts_review.csv
reports/eia860_2025_quality_summary.json
```

To explore preliminary ICP segmentation from the generated account review CSV:

```powershell
$env:PYTHONPATH = "src"
python -m energy_intel.classification
```

To run automated tests:

```powershell
python -m pytest -v
```

**Test coverage:** 37 passing test cases in the current local development milestone, covering text normalization, account transformation, plant association, basic data-quality flags, and preliminary ICP classification. The repository does not yet have a GitHub Actions test workflow.

On macOS/Linux, activate the environment with `source .venv/bin/activate` and set the import path with `export PYTHONPATH=src`.

## Repository layout

```text
src/energy_intel/
  loader.py             # Read EIA workbooks from the ZIP archive
  normalization.py      # Clean company-name whitespace
  schema.py             # Account schema and source field mappings
  transform.py          # Build standardized utility records
  association.py        # Count distinct plant associations
  quality.py            # Flag basic record-quality issues
  pipeline.py           # Main export pipeline and summary report
  validate_exports.py   # Reconcile exported CSV with JSON metrics
  classification.py     # Standalone exploratory ICP tiers
  profile_accounts.py   # Inspect source entity and plant distributions
  inspect_eia.py        # Source workbook inspection

tests/                   # pytest unit tests
reports/                 # Aggregate quality report
data/raw/                # Local source ZIP (Git-ignored)
data/processed/          # Generated account CSV (Git-ignored)
```

## Methodology and safeguards

- EIA **Utility ID** is retained as a string; identifiers should not be converted to numbers because their exact representation matters.
- The associated plant count uses **distinct Plant Codes per Utility ID**; duplicate records do not inflate the count.
- Quality flags identify records needing review. They do **not** automatically delete or merge accounts.
- Missing values are not silently replaced with unsupported assumptions.
- EIA `Entity Type` codes are interpreted using the definitions included in the archive's `LayoutY2025.xlsx` data dictionary.
- Preliminary ICP rules are **project-defined research criteria**, not EIA classifications. Geographic fit, asset ownership, active operating status, decision-maker relevance, and outreach suitability require further verification.

## Known limitations and next improvements

- Generator-level ownership analysis is not yet implemented; a reported plant association is not proof of ownership.
- The primary output is an **account review CSV**, not a contact-enriched or import-approved HubSpot dataset.
- Preliminary ICP tiers are deliberately broad; specific targeting requires additional rules and evidence.
- No API refresh/scheduling, version-pinned dependency lockfile, CI pipeline, or automated sample output publication yet.
- Next work: incorporate the ownership dataset, strengthen qualification logic and tests, integrate classification into exports, and add a small safe-to-share sample output and CI checks.

## Author

**Benedict Z. Castro** — Python automation, B2B account intelligence, data quality, and software engineering.

- [Professional portfolio](https://benicastro.github.io/benedict-portfolio/)
- [GitHub](https://github.com/benicastro)

*Independent project using public data. No client information or confidential source code is used.*
