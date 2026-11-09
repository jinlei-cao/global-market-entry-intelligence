"""Streamlit front-end; uses saved, disclosure-tagged experiments.

Run: streamlit run app/streamlit_app.py
"""
from __future__ import annotations
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
# Enables `streamlit run` from a fresh checkout before editable install.
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from marketintel.config import INDICATORS, WEIGHTS
from marketintel.scoring import rank_countries, weight_sensitivity

st.set_page_config(page_title="Global Market Entry Intelligence", page_icon="🌍", layout="wide")

st.markdown("""
<style>
[data-testid="stMetricValue"] {font-size:1.65rem;}
.block-container {padding-top:2.1rem;}
.smallnote {font-size:.9rem;color:#506259;}
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def load_run(path_string: str):
    path = ROOT / path_string
    if not path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("Experiment directory must be inside the project")
    required = ["analysis_manifest.json", "normalised_scores.csv", "country_rankings.csv",
                "source_observations.csv", "data_completeness.csv", "weight_robustness.csv"]
    absent = [filename for filename in required if not (path / filename).exists()]
    if absent:
        raise FileNotFoundError(f"Run `marketintel demo` or `marketintel analyze` first. Missing: {absent}")
    return ({"manifest": json.loads((path / required[0]).read_text(encoding="utf-8")),
             "normalised": pd.read_csv(path / required[1]),
             "rankings": pd.read_csv(path / required[2]),
             "observations": pd.read_csv(path / required[3]),
             "completeness": pd.read_csv(path / required[4]),
             "robustness": pd.read_csv(path / required[5])})

st.title("Global Market Entry Intelligence")
st.caption("Open-source quantitative research · Jinlei Cao · Country-level market screening")

with st.sidebar:
    st.header("Research controls")
    run_dir = st.selectbox("Experiment", ["reports/demo", "reports/latest"], index=0,
                           help="The latest run is available after executing the real-data pipeline.")
    st.caption("All scores are relative to the selected candidate set.")
try:
    run = load_run(run_dir)
except (FileNotFoundError, ValueError) as exc:
    st.error(str(exc))
    st.stop()

manifest = run["manifest"]
if manifest.get("is_synthetic"):
    st.error("SYNTHETIC DEMO — country values, scores, and rankings are fictional. This is an interface test, not empirical research.")
else:
    st.info("World Bank source observations. This is a preliminary comparison model, not investment, credit or legal advice.")

with st.sidebar:
    st.divider()
    st.subheader("Decision preferences")
    weights_raw = {}
    for ind in INDICATORS:
        weights_raw[ind.code] = st.slider(ind.label, 0, 100, int(round(100*WEIGHTS[ind.code])),
                                         key=f"weight_{ind.code}")
    total = sum(weights_raw.values())
    if total <= 0:
        st.warning("Set at least one weight above zero")
        st.stop()
    norm_weights = {code: v / total for code, v in weights_raw.items()}
    st.caption(f"Input total: {total}% — weights automatically normalised to 100%")
    n_sims = st.select_slider("Preference simulations", options=[200, 500, 1000, 2000], value=500)
    st.caption("Dirichlet perturbations vary the importance of criteria, not country data uncertainty.")

normalised = run["normalised"].set_index("iso3")
meta = run["rankings"][["iso3", "country"]].drop_duplicates()
updated = rank_countries(normalised, meta, norm_weights)
robust = weight_sensitivity(normalised, norm_weights, n_sim=n_sims, seed=42, concentration=55)
updated = updated.merge(robust[["iso3", "probability_rank_1", "mean_rank"]], on="iso3", how="left")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Countries ranked", str(len(updated)))
c2.metric("Highest relative score", f"{updated.iloc[0].weighted_sum:.1f} / 100")
c3.metric("Current #1 candidate", updated.iloc[0].country)
c4.metric("Source status", "Synthetic" if manifest.get("is_synthetic") else "World Bank")

st.caption("The top market is the highest-scoring **comparison candidate**, not an investment recommendation.")

tab1, tab2, tab3, tab4 = st.tabs(["Rankings & map", "Scoring drivers", "Data provenance", "Methods & caveats"])

with tab1:
    left, right = st.columns([1.25, 1])
    with left:
        bars = px.bar(updated.sort_values("weighted_sum").tail(15), x="weighted_sum", y="country",
                      orientation="h", color_discrete_sequence=["#276153"],
                      labels={"weighted_sum":"Weighted score / 100", "country":""})
        bars.update_layout(height=530, margin=dict(l=0,r=0,t=18,b=10), showlegend=False)
        st.plotly_chart(bars, use_container_width=True)
    with right:
        fig = go.Figure(go.Choropleth(locations=updated.iso3, z=updated.weighted_sum,
                   text=updated.country, colorscale="Greens", colorbar_title="Relative score",
                   marker_line_color="white", marker_line_width=.4))
        fig.update_geos(showcoastlines=True, coastlinecolor="lightgrey", showcountries=True,
                        countrycolor="lightgrey", projection_type="natural earth")
        fig.update_layout(height=530, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(updated.style.format({"weighted_sum":"{:.2f}", "topsis_closeness":"{:.3f}",
                                     "probability_rank_1":"{:.1%}", "mean_rank":"{:.2f}"}),
                 hide_index=True, use_container_width=True)
    st.download_button("Download current ranking (CSV)",
                       updated.to_csv(index=False).encode("utf-8"),
                       file_name="market_rankings_custom_weights.csv", mime="text/csv")

with tab2:
    chosen = st.selectbox("Inspect a comparison market", updated.country.tolist())
    chosen_iso3 = updated.loc[updated.country==chosen, "iso3"].iloc[0]
    contribution = pd.DataFrame({
        "indicator": [i.label for i in INDICATORS],
        "normalised_value": [normalised.loc[chosen_iso3, i.code] for i in INDICATORS],
        "weight": [norm_weights[i.code] for i in INDICATORS],
    })
    contribution["contribution"] = contribution.normalised_value * contribution.weight
    fig = px.bar(contribution, x="contribution", y="indicator", orientation="h",
                 color_discrete_sequence=["#276153"],
                 labels={"contribution":"Contribution to total weighted score", "indicator":""})
    fig.update_layout(height=410, margin=dict(l=0,r=0,t=10,b=0))
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(contribution.style.format({"normalised_value":"{:.1f}","weight":"{:.1%}",
                                           "contribution":"{:.1f}"}), hide_index=True, use_container_width=True)
    st.caption("Min-max normalisation gives 50 points to a constant indicator. GDP is log10-transformed. Country scores change if the candidate set changes.")

with tab3:
    st.subheader("Dated source observations")
    observations = run["observations"]
    st.dataframe(observations, use_container_width=True, hide_index=True)
    st.subheader("Completeness and exclusions")
    st.dataframe(run["completeness"], use_container_width=True, hide_index=True)
    st.download_button("Download source observation table", observations.to_csv(index=False).encode("utf-8"),
                       file_name="source_observations.csv", mime="text/csv")
    st.markdown("**Data provenance:** Source IDs, indicator years, the dataset type and original API URLs are recorded in the run manifest and source files.")

with tab4:
    st.markdown("""
**Research design**

1. Choose a disclosed set of emerging-market candidates. This set is **not** a verified roster of Belt and Road participants.
2. Obtain the most recent valid observation at or before the configured cut-off year and report its actual year.
3. Apply complete-case inclusion by default; optional median imputation is disclosed and should be stress-tested.
4. Transform GDP using log10; perform within-sample min-max normalisation of the five indicators.
5. Rank using weighted-sum scoring and a separate TOPSIS comparison.
6. Perturb preference weights with a Dirichlet distribution to assess ranking sensitivity to assumed priorities.

**Interpretation limitations**

- The historical LPI overall indicator is based on a 2023 logistics survey. It must not be mixed with the newer tracking-based LPI 2.0 as though they were the same measure.
- The World Bank's Worldwide Governance Indicators reflect survey/expert perceptions; they are not audited investment or credit risk ratings.
- Some metrics have different observation years; missingness, limited coverage and sample changes affect comparisons.
- Weight-sensitivity simulation models preferences only, not uncertainty in World Bank measurements or investment outcomes.
- Company-specific profits, sanctions, regulations, sector bans, environmental impacts and local legal review are outside the model.

**Research use:** A transparent quantitative starting point for an independently reviewed market-entry study. No country ranking by itself justifies allocating capital.
""")
    st.code("marketintel fetch && marketintel analyze --output reports/latest", language="bash")
    st.caption("Read docs/METHODOLOGY.md, docs/DATA_DICTIONARY.md and docs/REFERENCES_APA.md before citing results.")

st.divider()
st.caption("Open-source research portfolio · MIT licensed code · Attribution required for third-party data · Contact details kept private")
