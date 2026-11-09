"""Transparent multi-criteria market comparisons: screening, WSM, TOPSIS, robustness."""
from __future__ import annotations

import numpy as np
import pandas as pd
from .config import INDICATORS, WEIGHTS


class InputQualityError(ValueError):
    pass


def validate_weights(weights: dict[str, float] | None = None) -> dict[str, float]:
    weights = dict(WEIGHTS if weights is None else weights)
    codes = {ind.code for ind in INDICATORS}
    if set(weights) != codes:
        raise InputQualityError(f"Weights must match exactly these indicators: {sorted(codes)}")
    if any(not np.isfinite(float(x)) or float(x) < 0 for x in weights.values()):
        raise InputQualityError("Weights must be finite and nonnegative")
    total = sum(weights.values())
    if total <= 0:
        raise InputQualityError("At least one weight must be positive")
    return {key: float(val) / total for key, val in weights.items()}


def panel_to_matrix(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    required = {"iso3", "country", "indicator", "value", "year", "status"}
    missing = required.difference(panel.columns)
    if missing:
        raise InputQualityError(f"Missing columns: {sorted(missing)}")
    if panel.duplicated(["iso3", "indicator"]).any():
        raise InputQualityError("Duplicate country/indicator records")
    for ind in INDICATORS:
        if ind.code not in panel.indicator.values:
            raise InputQualityError(f"No rows for required indicator {ind.code}")
    meta = panel[["iso3", "country"]].drop_duplicates().set_index("iso3").sort_index()
    mat = panel.pivot(index="iso3", columns="indicator", values="value")
    mat = mat.reindex(columns=[x.code for x in INDICATORS]).sort_index()
    return mat, meta


def build_matrix(panel: pd.DataFrame, missing_policy: str = "exclude",
                 exclude: set[str] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Only observed complete-case countries are ranked unless explicit median imputation chosen."""
    if missing_policy not in {"exclude", "impute_median"}:
        raise InputQualityError("missing_policy must be exclude or impute_median")
    raw, meta = panel_to_matrix(panel)
    if exclude:
        raw = raw.loc[~raw.index.isin(exclude)]
        meta = meta.loc[meta.index.isin(raw.index)]
    if raw.empty:
        raise InputQualityError("No countries remain")
    diag = raw.isna().copy()
    miss = diag.sum(axis=1).rename("missing_indicators")
    if missing_policy == "exclude":
        mat = raw.dropna()
    else:
        if raw.isna().all(axis=0).any():
            raise InputQualityError("Cannot impute an indicator missing for all countries")
        mat = raw.fillna(raw.median(axis=0))
    if len(mat) < 2:
        raise InputQualityError("At least two countries with complete indicator values are required")
    missingness = meta.join(miss).reset_index()
    missingness["eligible"] = missingness.iso3.isin(mat.index)
    missingness["policy"] = missing_policy
    missingness["missing_indicator_codes"] = missingness.iso3.map(
        lambda iso: ", ".join(raw.columns[raw.loc[iso].isna()].tolist()))
    return mat, missingness


def normalize_matrix(mat: pd.DataFrame) -> pd.DataFrame:
    """Min-max 0–100 benefit scores; GDP receives log10 transform first.

    Constant columns are neutral (50), not artificially best/worst.
    Rankings are relative to the selected candidate set.
    """
    outputs = {}
    for ind in INDICATORS:
        if ind.code not in mat.columns:
            raise InputQualityError(f"Missing {ind.code}")
        x = pd.to_numeric(mat[ind.code], errors="coerce").astype(float)
        if not np.isfinite(x).all():
            raise InputQualityError(f"Nonfinite values in {ind.code}")
        if ind.transform == "log10":
            if (x <= 0).any():
                raise InputQualityError("GDP must be positive to apply log10")
            x = np.log10(x)
        mn, mx = float(x.min()), float(x.max())
        if np.isclose(mx, mn):
            out = pd.Series(50.0, index=x.index)
        else:
            out = (x - mn) / (mx - mn) * 100.0
        if ind.direction == "lower":
            out = 100.0 - out
        outputs[ind.code] = out
    return pd.DataFrame(outputs, index=mat.index)


def weighted_sum(normalized: pd.DataFrame, weights: dict[str, float] | None = None) -> pd.Series:
    w = validate_weights(weights)
    return normalized[list(w)].dot(pd.Series(w)).rename("weighted_sum")


def topsis(normalized: pd.DataFrame, weights: dict[str, float] | None = None) -> pd.Series:
    """TOPSIS on already direction-aligned 0-100 comparable criteria.

    Zero-distance edge cases return 0.5 neutral closeness.
    """
    w = validate_weights(weights)
    a = normalized[list(w)].to_numpy(dtype=float)
    length = np.sqrt((a*a).sum(axis=0))
    length = np.where(length == 0, 1.0, length)
    scaled = a / length * np.asarray(list(w.values()))
    ideal_best = scaled.max(axis=0)
    ideal_worst = scaled.min(axis=0)
    dplus = np.linalg.norm(scaled - ideal_best, axis=1)
    dminus = np.linalg.norm(scaled - ideal_worst, axis=1)
    denom = dplus + dminus
    proximity = np.divide(dminus, denom, out=np.full_like(dminus, 0.5), where=denom>0)
    return pd.Series(proximity, index=normalized.index, name="topsis_closeness")


def rank_countries(normalized: pd.DataFrame, metadata: pd.DataFrame,
                   weights: dict[str, float] | None = None) -> pd.DataFrame:
    wsm = weighted_sum(normalized, weights)
    top = topsis(normalized, weights)
    ranked = pd.DataFrame({"iso3": normalized.index, "weighted_sum": wsm.values,
                           "topsis_closeness": top.values})
    if "country" in metadata.columns:
        ranked["country"] = ranked.iso3.map(metadata.set_index("iso3")["country"])
    ranked = ranked.sort_values(["weighted_sum", "country"], ascending=[False, True]).reset_index(drop=True)
    ranked.insert(0, "rank", np.arange(1, len(ranked)+1))
    ranked["topsis_rank"] = ranked.topsis_closeness.rank(ascending=False, method="min").astype(int)
    return ranked[["rank", "iso3", "country", "weighted_sum", "topsis_rank", "topsis_closeness"]]


def weight_sensitivity(normalized: pd.DataFrame, weights: dict[str, float] | None = None,
                       n_sim: int = 1200, seed: int = 42,
                       concentration: float = 55) -> pd.DataFrame:
    """Dirichlet perturbation of *assumed* preference weights (not data uncertainty).

    Each simulation holds the normalised country values fixed. Results are conditional
    on the choice of indicators, study sample, imputation and selected weight prior.
    """
    w = validate_weights(weights)
    if not 50 <= n_sim <= 100000:
        raise InputQualityError("n_sim should be 50–100,000")
    if concentration <= 0:
        raise InputQualityError("concentration must be >0")
    rng = np.random.default_rng(seed)
    alpha = np.maximum(np.asarray(list(w.values())) * concentration, 0.001)
    sim_w = rng.dirichlet(alpha, size=n_sim)
    scores = normalized[list(w)].to_numpy(dtype=float) @ sim_w.T
    winners = scores.argmax(axis=0)
    ranks = np.argsort(np.argsort(-scores, axis=0), axis=0) + 1
    return pd.DataFrame({"iso3": normalized.index,
                         "probability_rank_1": np.bincount(winners, minlength=len(normalized))/n_sim,
                         "mean_rank": ranks.mean(axis=1),
                         "p10_score": np.percentile(scores, 10, axis=1),
                         "p50_score": np.percentile(scores, 50, axis=1),
                         "p90_score": np.percentile(scores, 90, axis=1)}).sort_values(
                            ["probability_rank_1", "mean_rank"], ascending=[False, True])
