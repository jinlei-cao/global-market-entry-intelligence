import numpy as np
import pandas as pd
import pytest

from marketintel.config import INDICATORS, WEIGHTS
from marketintel.data import generate_synthetic_panel
from marketintel.scoring import (InputQualityError, validate_weights, build_matrix,
                                 normalize_matrix, weighted_sum, topsis, rank_countries,
                                 weight_sensitivity)


def test_weights_sum_one():
    assert sum(validate_weights().values()) == pytest.approx(1.0)


def test_weight_negative_rejected():
    w = dict(WEIGHTS)
    w["RQ.EST"] = -1
    with pytest.raises(InputQualityError):
        validate_weights(w)


def test_nonzero_weights_required():
    with pytest.raises(InputQualityError):
        validate_weights({k: 0 for k in WEIGHTS})


def test_normalized_bounds():
    panel = generate_synthetic_panel()
    mat, _ = build_matrix(panel)
    norm = normalize_matrix(mat)
    assert norm.shape == (18, 5)
    assert np.isfinite(norm.to_numpy()).all()
    assert (norm >= -1e-9).all().all() and (norm <= 100+1e-9).all().all()


def test_constant_series_neutral():
    panel = generate_synthetic_panel()
    mat, _ = build_matrix(panel)
    mat["RQ.EST"] = 0.3
    norm = normalize_matrix(mat)
    assert np.allclose(norm["RQ.EST"], 50)


def test_gdp_log_nonpositive_rejected():
    panel = generate_synthetic_panel()
    mat, _ = build_matrix(panel)
    mat.loc[mat.index[0], "NY.GDP.MKTP.CD"] = 0
    with pytest.raises(InputQualityError):
        normalize_matrix(mat)


def test_weighted_sum_and_topsis_rank():
    panel = generate_synthetic_panel()
    mat, _ = build_matrix(panel)
    norm = normalize_matrix(mat)
    meta = panel[["iso3", "country"]].drop_duplicates()
    ranks = rank_countries(norm, meta)
    assert ranks["rank"].tolist() == list(range(1, 19))
    assert ranks["weighted_sum"].is_monotonic_decreasing
    assert ranks["topsis_closeness"].between(0, 1).all()


def test_missing_exclude_and_median_imputation():
    panel = generate_synthetic_panel()
    iso = panel.iso3.iloc[0]
    panel.loc[(panel.iso3 == iso) & (panel.indicator == "RQ.EST"), "value"] = np.nan
    mat, miss = build_matrix(panel, missing_policy="exclude")
    assert iso not in mat.index and miss.loc[miss.iso3==iso, "missing_indicators"].iloc[0] == 1
    mat2, miss2 = build_matrix(panel, missing_policy="impute_median")
    assert iso in mat2.index and mat2.notna().all().all()


def test_sensitivity_reproducible():
    panel = generate_synthetic_panel(seed=19)
    mat, _ = build_matrix(panel)
    norm = normalize_matrix(mat)
    x = weight_sensitivity(norm, n_sim=300, seed=19).set_index("iso3")
    y = weight_sensitivity(norm, n_sim=300, seed=19).set_index("iso3")
    pd.testing.assert_frame_equal(x, y)
    assert x.probability_rank_1.sum() == pytest.approx(1.0)


def test_prevent_duplicate_country_indicator():
    panel = generate_synthetic_panel()
    panel = pd.concat([panel, panel.head(1)], ignore_index=True)
    with pytest.raises(InputQualityError):
        build_matrix(panel)
