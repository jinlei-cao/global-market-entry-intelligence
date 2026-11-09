"""Experiment orchestration; every output carries a data-kind/provenance disclosure."""

from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .config import INDICATORS, WEIGHTS, DEFAULT_AS_OF
from .scoring import (InputQualityError, build_matrix, normalize_matrix,
                      rank_countries, weight_sensitivity, validate_weights)


def _detect_kind(path: Path, panel: pd.DataFrame) -> str:
    manifest_path = path.with_suffix(".manifest.json")
    if manifest_path.exists():
        kind = json.loads(manifest_path.read_text(encoding="utf-8")).get("kind")
        if kind == "synthetic_demo":
            return "synthetic_demo"
        if kind == "real_world_bank_observations":
            if panel["status"].astype(str).str.contains("SYNTHETIC", case=False).any():
                raise InputQualityError("Manifest claims real data but synthetic values are present")
            if not panel["source"].astype(str).eq("World Bank Indicators API").all():
                raise InputQualityError("Real manifest has unexpected source labels")
            return kind
        raise InputQualityError("Manifest kind unrecognised")
    # Protect against interpreting an unverified CSV as World Bank evidence.
    raise InputQualityError("No matching .manifest.json file; cannot certify dataset provenance")


def _build_figures(ranking: pd.DataFrame, robustness: pd.DataFrame,
                   out: Path, synthetic: bool) -> None:
    fig, ax = plt.subplots(figsize=(9.6, 6), dpi=140)
    top = ranking.head(12).iloc[::-1]
    ax.barh(top["country"], top["weighted_sum"], color="0.25")
    ax.set_xlabel("Relative weighted score (0–100)")
    ax.set_xlim(0, 105)
    ax.set_title("Illustrative market comparison" if synthetic else "World Bank indicator-based market comparison")
    if synthetic:
        fig.text(.5, .01, "SYNTHETIC DEMO — country values are invented for software testing",
                 ha="center", fontsize=9, color="0.4")
    else:
        fig.text(.5, .01, "Relative scores; not investment advice. Compare data years and completeness.",
                 ha="center", fontsize=9, color="0.4")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(out / "market_ranking.png", bbox_inches="tight")
    plt.close(fig)

    merged = ranking.merge(robustness, on="iso3")
    fig, ax = plt.subplots(figsize=(9.2, 5.5), dpi=140)
    ax.scatter(merged["weighted_sum"], merged["probability_rank_1"], c="0.2", s=50)
    for _, row in merged.iterrows():
        ax.annotate(row.iso3, (row.weighted_sum, row.probability_rank_1),
                    xytext=(3,3), textcoords="offset points", fontsize=7)
    ax.set_xlabel("Weighted sum (relative)")
    ax.set_ylabel("Share ranked first under simulated preferences")
    ax.set_ylim(-.04, 1.04)
    ax.set_title("Preference-weight sensitivity (not forecast uncertainty)")
    if synthetic:
        fig.text(.5,.01,"SYNTHETIC DEMO — no empirical conclusions",ha="center",fontsize=9,color="0.4")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(out / "weight_sensitivity.png", bbox_inches="tight")
    plt.close(fig)


def analyse(input_csv: Path, output: Path, missing_policy: str = "exclude",
            exclude_countries: set[str] | None = None,
            weights: dict[str, float] | None = None,
            n_sim: int = 1200, seed: int = 42,
            concentration: float = 55) -> dict:
    panel = pd.read_csv(input_csv)
    kind = _detect_kind(input_csv, panel)
    w = validate_weights(weights)
    mat, missingness = build_matrix(panel, missing_policy=missing_policy,
                                    exclude=exclude_countries)
    normalized = normalize_matrix(mat)
    metadata = panel[["iso3", "country"]].drop_duplicates()
    ranks = rank_countries(normalized, metadata, w)
    sensitivity = weight_sensitivity(normalized, w, n_sim=n_sim, seed=seed,
                                     concentration=concentration)
    sensitivity = sensitivity.merge(metadata, on="iso3", how="left")
    output.mkdir(parents=True, exist_ok=True)

    ranks.to_csv(output / "country_rankings.csv", index=False)
    normalized.rename_axis("iso3").reset_index().to_csv(output / "normalised_scores.csv", index=False)
    mat.rename_axis("iso3").reset_index().to_csv(output / "raw_values.csv", index=False)
    panel.to_csv(output / "source_observations.csv", index=False)
    missingness.to_csv(output / "data_completeness.csv", index=False)
    sensitivity.to_csv(output / "weight_robustness.csv", index=False)
    _build_figures(ranks, sensitivity, output, synthetic=kind=="synthetic_demo")
    manifest = {
        "data_kind": kind,
        "is_synthetic": kind == "synthetic_demo",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input": str(input_csv),
        "missing_policy": missing_policy,
        "countries_in_input": int(panel.iso3.nunique()),
        "countries_ranked": len(ranks),
        "excluded_country_codes": sorted(exclude_countries or set()),
        "weights": w,
        "sensitivity": {"simulations": n_sim, "seed": seed,
                        "dirichlet_concentration": concentration,
                        "interpretation": "Preference weights uncertainty only; country-indicator measurement uncertainty not modelled."},
        "model_limitations": [
            "Relative rankings depend on the candidate set and chosen indicator weights.",
            "LPI is the old survey-based indicator, not the LPI 2.0 tracking-data series.",
            "WGI regulatory-quality estimate is perception-based, not a regulatory audit.",
            "No firm-specific profitability, tax, legal, sanctions, or due-diligence screening.",
            "Different indicators can refer to different years; see source_observations.csv.",
            "Top-ranked markets are screening candidates, not investment recommendations."
        ],
    }
    (output / "analysis_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    leader = ranks.iloc[0]
    note = "**SYNTHETIC DEMONSTRATION — ALL INDICATOR VALUES ARE INVENTED.**" if manifest["is_synthetic"] else \
           "**LIVE WORLD BANK OBSERVATIONS — DESCRIPTIVE, NOT A VALIDATED INVESTMENT RATING.**"
    weight_lines = "\n".join(f"- {ind.label}: {100*w[ind.code]:.1f}%" for ind in INDICATORS)
    text = f"""# Research output — Global Market Entry Intelligence

{note}

## Scope

- Comparison set: {len(ranks)} ranked markets, chosen as **illustrative candidates**, not verified BRI membership.
- Data policy: `{missing_policy}`; missingness and dated observations saved separately.
- Highest relative weighted score: **{leader.country}** ({leader.weighted_sum:.2f}/100) within this candidate set.
- Scoring: within-sample min-max scaling; log-GDP; weighted sum and TOPSIS.
- Robustness: {n_sim} Dirichlet draws (concentration {concentration}, seed {seed}), varying **preferences only**.

## Assumed weights

{weight_lines}

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
"""
    (output / "RESULTS.md").write_text(text, encoding="utf-8")
    return manifest
