import pytest

from energy_intel.normalization import normalize_company_name


@pytest.mark.parametrize(
    "raw_name, expected",
    [
        ("  Example   Energy  LLC  ", "Example Energy LLC"),
        ("Northwind\tPower\nHoldings", "Northwind Power Holdings"),
        ("ACME, Inc.", "ACME, Inc."),
        ("", None),
        ("   ", None),
        (None, None),
    ],
)
def test_normalize_company_name(raw_name, expected):
    assert normalize_company_name(raw_name) == expected
