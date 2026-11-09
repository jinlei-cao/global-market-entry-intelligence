import json
import pandas as pd
import pytest

from marketintel.data import write_demo_panel
from marketintel.experiment import analyse
from marketintel.scoring import InputQualityError


def test_demo_generates_required_files(tmp_path):
    inp = tmp_path / "data" / "synthetic.csv"
    write_demo_panel(inp, seed=3)
    out = tmp_path / "reports" / "demo"
    metadata = analyse(inp, out, n_sim=200, seed=3)
    assert metadata["is_synthetic"]
    for filename in ["country_rankings.csv", "normalised_scores.csv", "source_observations.csv",
                     "data_completeness.csv", "weight_robustness.csv", "market_ranking.png",
                     "weight_sensitivity.png", "analysis_manifest.json", "RESULTS.md"]:
        assert (out / filename).is_file()
    assert "SYNTHETIC DEMONSTRATION" in (out / "RESULTS.md").read_text()


def test_missing_manifest_blocks_research_claim(tmp_path):
    inp = tmp_path / "fabricated.csv"
    write_demo_panel(inp)
    inp.with_suffix(".manifest.json").unlink()
    with pytest.raises(InputQualityError):
        analyse(inp, tmp_path / "out", n_sim=200)


def test_manifest_kind_prevents_synthetic_as_real(tmp_path):
    inp = tmp_path / "data.csv"
    write_demo_panel(inp)
    path = inp.with_suffix(".manifest.json")
    data = json.loads(path.read_text())
    data["kind"] = "real_world_bank_observations"
    path.write_text(json.dumps(data))
    with pytest.raises(InputQualityError):
        analyse(inp, tmp_path / "out", n_sim=200)
