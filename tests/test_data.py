import numpy as np
import pandas as pd
import pytest

from marketintel.config import COUNTRIES, INDICATORS
from marketintel.data import parse_api_records, select_latest_observations, generate_synthetic_panel


def test_world_bank_api_response_parser():
    example = [{"pages":1,"total":3}, [
        {"countryiso3code":"IDN", "date":"2024", "value":180.0},
        {"countryiso3code":"IDN", "date":"2023", "value":None},
        {"countryiso3code":"VNM", "date":"2022", "value":"15"}]]
    rows = parse_api_records(example, "IT.NET.USER.ZS")
    assert len(rows) == 2
    assert rows[0]["year"] == 2024
    assert rows[1]["value"] == 15


def test_world_bank_errors_fail_loudly():
    with pytest.raises(ValueError):
        parse_api_records({"message":["Invalid indicator"]}, "FOO")


def test_latest_year_and_staleness():
    records = [
        {"iso3":"IDN", "year":2023, "indicator":"LP.LPI.OVRL.XQ", "value":3.0},
        {"iso3":"IDN", "year":2018, "indicator":"IT.NET.USER.ZS", "value":70.0},
        {"iso3":"IDN", "year":2026, "indicator":"NY.GDP.MKTP.CD", "value":1e10},
    ]
    result = select_latest_observations(records, as_of=2025, countries={"IDN":"Indonesia"})
    lpi = result[result.indicator=="LP.LPI.OVRL.XQ"].iloc[0]
    internet = result[result.indicator=="IT.NET.USER.ZS"].iloc[0]
    gdp = result[result.indicator=="NY.GDP.MKTP.CD"].iloc[0]
    assert lpi.year == 2023 and lpi.status == "observed"
    assert internet.status == "stale" and pd.isna(internet.value)
    assert pd.isna(gdp.value)  # future data excluded


def test_synthetic_seed_reproducible():
    x = generate_synthetic_panel(seed=85)
    y = generate_synthetic_panel(seed=85)
    pd.testing.assert_frame_equal(x, y)
    assert len(x) == len(COUNTRIES)*len(INDICATORS)
    assert x.source.str.contains("SYNTHETIC").all()
