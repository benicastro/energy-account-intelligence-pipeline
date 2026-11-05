
"""Data contracts for the EIA account intelligence pipeline."""

SOURCE_YEAR = 2025
SOURCE_NAME = "EIA-860"

# Map original EIA utility columns to standardized fields.
UTILITY_FIELD_MAP = {
    "Utility ID": "account_id",
    "Utility Name": "account_name",
    "Entity Type": "entity_type_code",
    "City": "city",
    "State": "state",
    "Zip": "postal_code",
    "Owner of Plants Reported on Form?": "reports_plant_ownership",
    "Operator of Plants Reported on Form?": "reports_plant_operation",
}

# Fields needed to associate reported plants with utilities.
PLANT_FIELD_MAP = {
    "Utility ID": "account_id",
    "Plant Code": "plant_id",
}

# Final column order for our initial account dataset.
ACCOUNT_COLUMNS = [
    "account_id",
    "account_name",
    "entity_type_code",
    "city",
    "state",
    "postal_code",
    "reports_plant_ownership",
    "reports_plant_operation",
    "associated_plant_count",
    "source_year",
    "source_name",
]
