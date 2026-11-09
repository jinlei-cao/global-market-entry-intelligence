# Data dictionary and sources

The repository uses the World Bank Indicators API (V2). `source=2` selects the World Development Indicators source; `source=3` selects the Worldwide Governance Indicators source for `RQ.EST`.

| Indicator | Interpretation | Caveat |
|---|---|---|
| `NY.GDP.MKTP.CD` | GDP in current US dollars | Currency conversion and price levels affect size; log-transform in scoring |
| `NY.GDP.MKTP.KD.ZG` | Real GDP growth, annual percentage | Business-cycle volatility; a high one-year growth value is not a forecast |
| `RQ.EST` | Regulatory quality estimate, WGI | Aggregates perceptions; measurement uncertainty; not a certified legal-risk score |
| `LP.LPI.OVRL.XQ` | Survey-based Logistics Performance Index, 1–5 | 2023 was the last survey edition; not equivalent to LPI 2.0 shipment tracking |
| `IT.NET.USER.ZS` | Individuals using the internet (% population) | National rate may mask substantial digital access differences |

The default source snapshot is `as_of_year=2025`, and data freshness varies by indicator and country. If an indicator has no recent non-null observations, `status=stale` or `unavailable` and `value` is missing. The `source_observations.csv` report records actual dates and labels.

## Citation and licensing

- World Bank API: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
- World Development Indicators: https://databank.worldbank.org/source/world-development-indicators
- Worldwide Governance Indicators, 2026 update: https://www.worldbank.org/en/publication/worldwide-governance-indicators
- Historical 2023 LPI: https://lpi.worldbank.org/en/indicators/survey-based-lpi-2007-2023
- LPI 2.0 overview (a separate methodology): https://lpi.worldbank.org/en/about

Use original World Bank data and terms of use for data publication. This repository does not commit a scraped or copied World Bank database, and the MIT software license does not claim ownership of third-party datasets.

## Study sample

The default country basket is maintained in `src/marketintel/config.py`. The list is a research sample for learning country-comparison methods, not an authoritative list of signatories to any international programme. The geographic unit is the World Bank ISO3 country series. A company-specific study should justify the market selection independently.
