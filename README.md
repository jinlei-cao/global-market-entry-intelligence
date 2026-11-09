# Global Market Entry Intelligence

**Comparing investment attractiveness and operational conditions across emerging markets with reproducible World Bank indicators**  
A quantitative decision-research portfolio for **Jinlei Cao**.

> **Status — v0.1.0.** The offline demo is entirely **synthetic**. Real rankings can be produced only after running the live World Bank download and analysis commands. No countries' real performance or investment prospects are asserted by the demo.

## Research problem

How can a company screen a shortlist of overseas markets using a transparent mix of market size, growth, regulatory environment, logistics and digital readiness? How sensitive are its priorities to subjective preferences about these criteria?

This is a **market-screening demonstration**, not an investment recommendation. It extends the analytical themes of international economics, outward investment, operations and decision analysis toward a replicable software and research workflow.

## Preview of the workflow

```text
World Bank WDI / WGI / historical LPI indicators
               |
      Latest valid date <= 2025
               |
        Completeness review
               |
       Country comparisons
               |
   Relative min-max normalisation
         + log-GDP transform
               |
      Weighted sum + TOPSIS
               |
    Preference-weight sensitivity
               |
     Streamlit interactive map
         + research tables
```

### Scientific design

- **Source-aware collection.** Official World Bank API source IDs and selected observation years are recorded in the output. The API requires internet for real-data collection.
- **Time honesty.** Use each indicator's latest valid year no later than the research cut-off (default 2025); retain observation year and exclude measurements exceeding predeclared age limits.
- **No false LPI equivalence.** This model uses `LP.LPI.OVRL.XQ`, the historical *survey-based* Logistics Performance Index; the newer 2023–2024 LPI 2.0 is a different tracking-based methodology and is not substituted into the score.
- **Governance caution.** `RQ.EST` is a perception-based Worldwide Governance Indicator, not a definitive investment-risk score.
- **Transparent preference weights.** Baseline: GDP 23%, growth 12%, regulatory quality 23%, logistics 25%, internet usage 17%. Alternative weights are research scenarios, not objectively correct preferences.
- **Dual ranking models.** Weighted-sum scoring and TOPSIS; country ranking is relative to the comparison basket.
- **Sensitivity analysis.** Dirichlet weight simulation assesses preferences only, not the accuracy or volatility of observed indicator values.
- **Missingness reporting.** Complete cases are the default. An optional median-imputation variant is labelled and should only be used as a sensitivity analysis.

## Run locally (Python 3.10+)

```bash
# Extract the ZIP. Open a terminal in the top-level project folder.
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[app,dev]'

# 1. Offline, fully synthetic demonstration — no web connection
marketintel demo

# 2. Run interactive country-rank / score / sensitivity dashboard
streamlit run app/streamlit_app.py
```

The dashboard starts in **reports/demo**, clearly marked *SYNTHETIC DEMO*. The supplied demo charts and rankings are invented for testing the software; they must not be quoted as observations about the named countries.

### Real-data experiment

```bash
# Internet required. Fetches official World Bank API data with dated provenance.
marketintel fetch

# Reproduce a preliminary comparison and sensitivity analysis.
marketintel analyze --input data/processed/world_bank_market_panel.csv --output reports/latest

# The Streamlit sidebar can now select reports/latest.
streamlit run app/streamlit_app.py
```

Country and indicator coverage vary by source. The real-data pipeline may exclude countries with missing or stale observations; inspect `reports/latest/data_completeness.csv` before interpreting rankings. API connectivity, indicator changes, or licensing policies can affect the download. See [DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md).

### Alternative research scenarios

```bash
# Exclude specified candidate ISO3 codes; document why exclusion is appropriate.
marketintel analyze --exclude PAK ETH --output reports/scenarios/a

# Explicit missing-data sensitivity analysis — median imputation is a modeling assumption.
marketintel analyze --missing-policy impute_median --output reports/scenarios/imputed

# Change preferences and sample the preference-weight distribution.
marketintel analyze --weight-market-size 0.30 --weight-growth 0.10 \
  --weight-governance 0.25 --weight-logistics 0.20 --weight-digital 0.15 \
  --simulations 2000 --output reports/scenarios/new-weights
```

The candidate basket is **illustrative emerging markets**; it should not be represented as a verified roster of Belt and Road Initiative signatories. Industry-specific market entry demands local regulation checks, company-specific costs and supply-chain feasibility beyond the available indicators.

## Project outputs

| Output | Meaning |
|---|---|
| `data/processed/world_bank_market_panel.csv` | Real data, downloaded only when `marketintel fetch` runs; intentionally git-ignored |
| `reports/demo/` | Included fictional example to test the dashboard |
| `reports/latest/` | Locally generated observed-data results; git-ignored until independently reviewed |
| `country_rankings.csv` | Weighted-sum and TOPSIS relative rankings |
| `raw_values.csv` | The selected observation values |
| `normalised_scores.csv` | The five 0–100 scaled model inputs |
| `source_observations.csv` | Indicator values, years, age, provenance and status |
| `data_completeness.csv` | Missingness and eligibility decisions |
| `weight_robustness.csv` | Preference-weight perturbation results |
| `market_ranking.png` | Candidate-score comparison |
| `weight_sensitivity.png` | Baseline scores vs rank-one frequency under varied preferences |
| `analysis_manifest.json` | Assumptions, data kind, weights, seed, exclusions and model caveats |
| `RESULTS.md` | Auto-generated research narrative with explicit synthetic/observed label |

## Suggested repository tree

```text
global-market-entry-intelligence/
├── README.md
├── LICENSE
├── CITATION.cff
├── pyproject.toml
├── requirements.txt
├── src/marketintel/
│   ├── config.py           # Candidate basket and indicator model
│   ├── data.py             # World Bank API / synthetic demo
│   ├── scoring.py          # Normalisation, weighted-sum, TOPSIS, sensitivity
│   ├── experiment.py       # Reports, provenance, plots
│   └── cli.py              # Command-line orchestration
├── app/streamlit_app.py    # Interactive world map and research UI
├── notebooks/01_research_walkthrough.ipynb
├── tests/                  # Offline repeatability & integrity checks
├── reports/demo/           # Clearly identified synthetic results
├── docs/                   # Research protocol, APA sources, limits
├── data/                   # Raw / observed data are not committed
└── .github/workflows/tests.yml
```

## Research limitations

This study ranks countries **only relative to the chosen set, data series and preference assumptions**. A changed comparison basket can change min–max scores. Different indicators may refer to different years. WGI reflects perception-based estimates, while survey LPI is a historical assessment. Cross-country indicators may hide within-country variation. The model does not measure causal effects, company-specific revenue, profitability, sanctions exposure, foreign ownership rules, contract enforcement, tax, or environmental harms. Investment choices require independent legal and sector due diligence.

## Research references

World Bank. (n.d.). *World Development Indicators*. https://databank.worldbank.org/source/world-development-indicators

World Bank. (2023). *Connecting to compete 2023: Trade logistics in the global economy—The Logistics Performance Index and its indicators*. https://lpi.worldbank.org/report

World Bank. (2026). *Worldwide Governance Indicators: 2026 update*. https://www.worldbank.org/en/publication/worldwide-governance-indicators

World Bank. (n.d.). *World Bank Indicators API documentation*. https://datahelpdesk.worldbank.org/knowledgebase/articles/889392

See [REFERENCES_APA.md](docs/REFERENCES_APA.md) for sources, versions and citation notes.
