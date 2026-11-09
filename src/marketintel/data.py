"""World Bank API access, defensive parsing, as-of-year observations, and offline demo data."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import time
from typing import Any

import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import COUNTRIES, DEFAULT_AS_OF, INDICATORS, Indicator

BASE_URL = "https://api.worldbank.org/v2"


def api_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "global-market-entry-intelligence/0.1 (academic research)"})
    retry = Retry(total=4, connect=4, read=4, backoff_factor=0.6,
                  status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=("GET",))
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def parse_api_records(payload: Any, indicator_code: str) -> list[dict]:
    """Convert paginated WDI/WGI response payload to observation records.

    World Bank responds [pagination_metadata, records] or {message:...} on errors.
    """
    if not isinstance(payload, list) or len(payload) != 2 or not isinstance(payload[1], list):
        raise ValueError(f"World Bank response for {indicator_code} was not a data array: {str(payload)[:250]}")
    results: list[dict] = []
    for item in payload[1]:
        if not isinstance(item, dict):
            continue
        iso3 = item.get("countryiso3code")
        year = item.get("date")
        value = item.get("value")
        if not (isinstance(iso3, str) and len(iso3) == 3):
            continue
        if value is None:
            continue
        try:
            year_int = int(year)
            value_float = float(value)
        except (ValueError, TypeError):
            continue
        if not np.isfinite(value_float):
            continue
        results.append({"iso3": iso3.upper(), "year": year_int,
                        "indicator": indicator_code, "value": value_float})
    return results


def fetch_one_indicator(session: requests.Session, indicator: Indicator,
                        iso3_list: list[str], as_of: int = DEFAULT_AS_OF) -> tuple[list[dict], list[str]]:
    if not iso3_list:
        return [], []
    country_url = ";".join(iso3_list)
    url = f"{BASE_URL}/country/{country_url}/indicator/{indicator.code}"
    params = {"format": "json", "date": f"2017:{as_of}", "per_page": 20000,
              "source": indicator.source}
    all_results: list[dict] = []
    page = 1
    retrieved_urls: list[str] = []
    while True:
        params["page"] = page
        response = session.get(url, params=params, timeout=35)
        response.raise_for_status()
        retrieved_urls.append(response.url)
        payload = response.json()
        parsed = parse_api_records(payload, indicator.code)
        all_results.extend(parsed)
        total_pages = int(payload[0].get("pages", 1))
        if page >= total_pages:
            break
        if page >= 20:
            raise ValueError("Too many World Bank pages; inspect API response and query")
        page += 1
    return all_results, retrieved_urls


def select_latest_observations(records: list[dict], as_of: int,
                               countries: dict[str, str] | None = None,
                               indicators: tuple[Indicator, ...] = INDICATORS) -> pd.DataFrame:
    """One record per country, indicator; retain age, source and missing values.

    Value is NaN when a valid observation is older than max_age or not available.
    """
    countries = countries or COUNTRIES
    df = pd.DataFrame(records, columns=["iso3", "year", "indicator", "value"])
    result = []
    for iso3, name in countries.items():
        for indicator in indicators:
            if df.empty:
                matching = pd.DataFrame()
            else:
                matching = df.loc[(df.iso3 == iso3) & (df.indicator == indicator.code)
                                  & (df.year <= as_of)].sort_values("year", ascending=False)
            if matching.empty:
                year, val, age, status = None, np.nan, None, "unavailable"
            else:
                top = matching.iloc[0]
                year = int(top.year)
                age = as_of - year
                val = float(top.value) if age <= indicator.max_age else np.nan
                status = "observed" if age <= indicator.max_age else "stale"
            result.append({"iso3": iso3, "country": name, "indicator": indicator.code,
                           "indicator_label": indicator.label, "year": year,
                           "age_years": age, "value": val, "status": status,
                           "source": "World Bank Indicators API",
                           "source_id": indicator.source})
    return pd.DataFrame(result)


def download_country_panel(output: Path, as_of: int = DEFAULT_AS_OF,
                           countries: dict[str, str] | None = None,
                           session: requests.Session | None = None) -> tuple[pd.DataFrame, dict]:
    """Download live data and write a documented JSON manifest next to the CSV.

    Fails loudly when the World Bank source is inaccessible or when all values are missing.
    """
    if not (2000 <= as_of <= datetime.now(timezone.utc).year):
        raise ValueError("as_of must be between 2000 and the current calendar year")
    countries = countries or COUNTRIES
    if any(len(k) != 3 for k in countries):
        raise ValueError("Country IDs must be ISO3-style identifiers")
    session = session or api_session()
    all_records: list[dict] = []
    urls: dict[str, list[str]] = {}
    for indicator in INDICATORS:
        records, pages = fetch_one_indicator(session, indicator, list(countries), as_of)
        all_records.extend(records)
        urls[indicator.code] = pages
    panel = select_latest_observations(all_records, as_of, countries)
    if not panel.value.notna().any():
        raise RuntimeError("No usable observations obtained; inspect API availability and source IDs")
    output.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(output, index=False)
    metadata = {"kind": "real_world_bank_observations", "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "as_of_year": as_of, "candidate_set": "illustrative; not verified BRI membership",
                "api_requests": urls,
                "indicator_source": {ind.code: {"label": ind.label, "source_id": ind.source,
                                                    "max_age": ind.max_age} for ind in INDICATORS},
                "methodology": "Latest non-null observation no later than as_of_year, subject to age limits.",
                "note": "WGI is perception-based and LPI uses the historical survey methodology. Do not conflate LPI 2.0."}
    manifest = output.with_suffix(".manifest.json")
    manifest.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    return panel, metadata


def generate_synthetic_panel(seed: int = 2027, as_of: int = DEFAULT_AS_OF,
                             countries: dict[str, str] | None = None) -> pd.DataFrame:
    """Fully synthetic values for interface testing — no empirical market information."""
    countries = countries or COUNTRIES
    rng = np.random.default_rng(seed)
    latents = rng.normal(size=(len(countries), 3))
    output = []
    for ix, (iso3, name) in enumerate(countries.items()):
        m, institution, digital = latents[ix]
        specs = {
            "NY.GDP.MKTP.CD": float(10 ** np.clip(10.2 + 0.5 * m + rng.normal(0, 0.12), 8, 12)),
            "NY.GDP.MKTP.KD.ZG": float(np.clip(3.2 + 1.5*m + rng.normal(0, 1.5), -8, 15)),
            "RQ.EST": float(np.clip(-0.1 + 0.65*institution + rng.normal(0, 0.4), -2.5, 2.5)),
            "LP.LPI.OVRL.XQ": float(np.clip(2.8 + .32*institution + .1*digital + rng.normal(0, 0.16), 1, 5)),
            "IT.NET.USER.ZS": float(np.clip(55 + 14*digital + 4*institution + rng.normal(0, 4), 0, 100)),
        }
        for ind in INDICATORS:
            # Make LPI 2023 to accurately illustrate historic survey timing.
            year = 2023 if ind.code == "LP.LPI.OVRL.XQ" else as_of - int(rng.integers(0, 3))
            output.append({"iso3": iso3, "country": name, "indicator": ind.code,
                           "indicator_label": ind.label, "year": year,
                           "age_years": as_of - year, "value": specs[ind.code],
                           "status": "SYNTHETIC", "source": "SYNTHETIC / NOT WORLD BANK DATA",
                           "source_id": -1})
    return pd.DataFrame(output)


def write_demo_panel(output: Path, seed: int = 2027, as_of: int = DEFAULT_AS_OF) -> pd.DataFrame:
    panel = generate_synthetic_panel(seed=seed, as_of=as_of)
    output.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(output, index=False)
    output.with_suffix('.manifest.json').write_text(json.dumps({
        "kind": "synthetic_demo", "seed": seed, "as_of_year": as_of,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "warning": "Entire dataset is randomly generated. Country labels do not imply any actual country conditions."
    }, indent=2), encoding="utf-8")
    return panel
