# Methodology and reproducibility protocol

## Research question and status

This project demonstrates a structured, transparent *screening* model for evaluating prospective foreign markets. It does not claim to estimate investment returns or to identify legally investable markets. The target population is a disclosed illustrative sample of 18 emerging-market candidates. Membership in the Belt and Road Initiative is not certified by this candidate list.

## Indicators and assumptions

| Code | Construct | Weight | Direction | Source | Allowed years old |
|---|---|---:|---|---|---:|
| NY.GDP.MKTP.CD | GDP (current USD), log10 | 0.23 | Higher | WDI source ID 2 | 4 |
| NY.GDP.MKTP.KD.ZG | Annual real GDP growth (%) | 0.12 | Higher | WDI source ID 2 | 4 |
| RQ.EST | Regulatory quality estimate | 0.23 | Higher | WGI source ID 3 | 4 |
| LP.LPI.OVRL.XQ | Historical survey-based logistics performance | 0.25 | Higher | WDI source ID 2 | 5 |
| IT.NET.USER.ZS | Internet users (% of population) | 0.17 | Higher | WDI source ID 2 | 4 |

Weights are analyst assumptions; they are not elicited from an actual investing enterprise. The as-of-year is 2025 by default, with source data selected at or before the year. The 2023 LPI survey-based score is older and methodologically distinct from the 2023–2024 LPI 2.0 tracking-data indicators. This tool does not combine them.

## Sourcing and time controls

`marketintel fetch` makes explicit World Bank API calls; response URLs, indicator IDs and time caps are written to a manifest. The selector finds the latest valid annual observation for each country/indicator no later than the study cut-off. Measurements older than the prespecified indicator-specific age cap are marked stale and excluded from the main numeric matrix. The main model uses complete cases; an optional imputed analysis replaces missing observations with a cross-country median and labels this assumption.

**Limitation:** Latest-year selection is not a perfectly aligned cross-section. A weighted total implicitly combines measurements from different calendar years. Report each individual year beside every input.

## Country screening

The sample is a strategic comparison basket, not an official BRI affiliation list. Actual business feasibility screening should precede country comparison and examine sanctions, ownership permissions, investment agreements, licensing, capital controls, exchange rate risk, environmental/social consequences, trade barriers and market-specific sector restrictions. This software supports manual exclusions but cannot replace those legal and commercial checks.

## Normalisation

For each indicator, among eligible countries, apply

`z_ic = 100 * (x_ic - min_i x) / (max_i x - min_i x)`

The GDP series first receives a `log10` transform to avoid the largest economy dominating solely because of linear scale. All metrics used in this version are benefit-oriented. If a series is constant across markets, each receives 50 points (neutral). This procedure produces **relative scores**; changing the candidate set changes the min/max bounds and thus scores. The within-sample method should never be described as an externally calibrated investment-risk scale.

## Weighted-sum model

For country `c`, `S_c = sum_i w_i * z_ic`. Weights are normalised to a positive total of one, which makes the result interpretable as 0–100 relative score. The baseline has five weights set in `config.py`. A business stakeholder would need to establish domain-specific weights and hard constraints.

## TOPSIS comparison

Normalised benefit scores are vector-normalised by criterion, scaled by the same weight vector, and compared by Euclidean distance to the ideal-best and ideal-worst alternatives. The closeness coefficient `D_minus/(D_plus + D_minus)` ranges 0–1, with 0.5 assigned only to degenerate equal-distance cases. TOPSIS is used as an alternative ranking, not proof that a market is superior.

## Preference sensitivity

The Monte Carlo procedure samples a Dirichlet distribution with concentration parameters proportional to the baseline weight vector. The research output reports how frequently each country ranks first under these plausible *hypothetical preference changes*. It does not model confidence intervals in source data, country event risk, financial return, or real-world operational volatility. Simulations are deterministic for the given random seed.

## Reporting and interpretation

A complete reproducible report must publish source table, observation years, missingness/exclusion status, raw matrix, normalised matrix, weights, two rankings, simulated preference sensitivity and caveats. These artifacts are automatically written to the experiment folder.

## Research integrity

The offline demo is entirely synthetic, independent of the country labels. The analysis requires a companion `.manifest.json` file to prevent unlabelled arbitrary CSV files from silently being interpreted as observed World Bank data. Software outputs may still contain measurement error and require independent source verification. A reviewer should rerun the data collection and experiment and inspect the results before using any figures in an application.
