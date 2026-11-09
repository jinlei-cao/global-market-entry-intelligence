# Research output — Global Market Entry Intelligence

**SYNTHETIC DEMONSTRATION — ALL INDICATOR VALUES ARE INVENTED.**

## Scope

- Comparison set: 18 ranked markets, chosen as **illustrative candidates**, not verified BRI membership.
- Data policy: `exclude`; missingness and dated observations saved separately.
- Highest relative weighted score: **Pakistan** (82.88/100) within this candidate set.
- Scoring: within-sample min-max scaling; log-GDP; weighted sum and TOPSIS.
- Robustness: 1200 Dirichlet draws (concentration 55, seed 2027), varying **preferences only**.

## Assumed weights

- Market size: GDP (current US$): 23.0%
- Real GDP growth (%): 12.0%
- Regulatory quality (WGI estimate): 23.0%
- Logistics Performance Index (survey): 25.0%
- Internet users (% of population): 17.0%

## Files

- `source_observations.csv` — country, indicator, observation year, source, status.
- `data_completeness.csv` — excluded or imputed entries.
- `raw_values.csv` — raw metric values used for ranking.
- `normalised_scores.csv` — comparable scores (0–100).
- `country_rankings.csv` — weighted and TOPSIS ranks.
- `weight_robustness.csv` — preference-weight rank variation.
- `market_ranking.png`, `weight_sensitivity.png` — plots.
- `analysis_manifest.json` — full reproducibility configuration and disclosure.

## Cautions

These outputs illustrate a decision-support screening process. The model is conditional on the
candidate set, indicators, reference dates, missing-data treatment and preferences. World Bank
LPI (2023) is the historic survey series; LPI 2.0 is a separate shipping-data framework.
WGI estimates are perception-based. Regulatory feasibility, investment restrictions,
firm-specific financial projections and independent legal due diligence need separate work.

## Reproduction

Run `marketintel demo` for synthetic data, or `marketintel fetch && marketintel analyze`
for observed World Bank series. Project documentation explains data and methods.
