"""Profile EIA-860 accounts before ICP qualification."""

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = (
    PROJECT_ROOT
    / "data/processed/eia860_2025_accounts_review.csv"
)


def show_distribution(df, column, title):
    """Display the frequency of each reported value."""

    values = (
        df[column]
        .astype("string")
        .str.strip()
        .fillna("")
        .replace("", "(blank)")
    )

    print(f"\n{title}")
    print("-" * 55)

    for value, count in values.value_counts().items():
        print(f"{value}: {count:,}")


def main():
    accounts = pd.read_csv(
        CSV_PATH,
        dtype="string",
        keep_default_na=False,
    )

    print("\nEIA-860 ACCOUNT QUALIFICATION PROFILE")
    print("=" * 55)
    print(f"Total accounts: {len(accounts):,}")

    # Inspect the source's organization classifications.
    show_distribution(
        accounts,
        "entity_type_code",
        "ENTITY TYPE CODES",
    )

    # Inspect reported relationships with generating plants.
    show_distribution(
        accounts,
        "reports_plant_ownership",
        "REPORTED PLANT OWNERSHIP INDICATOR",
    )

    show_distribution(
        accounts,
        "reports_plant_operation",
        "REPORTED PLANT OPERATION INDICATOR",
    )

    # Profile associated plant counts.
    counts = pd.to_numeric(
        accounts["associated_plant_count"].replace("", pd.NA),
        errors="raise",
    )

    print("\nASSOCIATED PLANT COUNT DISTRIBUTION")
    print("-" * 55)

    ranges = [
        ("No matching plants", counts == 0),
        ("1 plant", counts == 1),
        ("2–4 plants", counts.between(2, 4)),
        ("5–19 plants", counts.between(5, 19)),
        ("20+ plants", counts >= 20),
    ]

    for label, condition in ranges:
        print(f"{label}: {int(condition.sum()):,}")

    print("\nIMPORTANT")
    print("-" * 55)
    print("These are descriptive statistics, not ICP decisions.")
    print("Plant associations do not establish ownership.")
    print("Entity codes must be interpreted using EIA definitions.")


if __name__ == "__main__":
    main()
