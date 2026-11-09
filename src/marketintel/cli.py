"""User-facing command line utility for research reproduction."""
from __future__ import annotations
import argparse
from pathlib import Path
import json
from .config import DEFAULT_AS_OF, INDICATORS
from .data import write_demo_panel, download_country_panel
from .experiment import analyse


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="marketintel", description="Reproducible market-entry research")
    sub = p.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo", help="Offline SYNTHETIC data and dashboard outputs")
    demo.add_argument("--seed", type=int, default=2027)
    demo.add_argument("--output", type=Path, default=Path("reports/demo"))
    fetch = sub.add_parser("fetch", help="Download dated World Bank observations (internet required)")
    fetch.add_argument("--as-of", type=int, default=DEFAULT_AS_OF)
    fetch.add_argument("--output", type=Path, default=Path("data/processed/world_bank_market_panel.csv"))
    run = sub.add_parser("analyze", help="Rank country values in a verified-provenance panel")
    run.add_argument("--input", type=Path, default=Path("data/processed/world_bank_market_panel.csv"))
    run.add_argument("--output", type=Path, default=Path("reports/latest"))
    run.add_argument("--missing-policy", choices=["exclude", "impute_median"], default="exclude")
    run.add_argument("--exclude", nargs="*", default=[], metavar="ISO3")
    run.add_argument("--weight-market-size", type=float, default=.23)
    run.add_argument("--weight-growth", type=float, default=.12)
    run.add_argument("--weight-governance", type=float, default=.23)
    run.add_argument("--weight-logistics", type=float, default=.25)
    run.add_argument("--weight-digital", type=float, default=.17)
    run.add_argument("--simulations", type=int, default=1200)
    run.add_argument("--seed", type=int, default=42)
    return p


def main(args: list[str] | None = None):
    a = parser().parse_args(args)
    if a.command == "fetch":
        panel, meta = download_country_panel(a.output, as_of=a.as_of)
        print(f"Downloaded {len(panel)} country-indicator rows; {panel.value.notna().sum()} usable observations -> {a.output}")
        print("Source metadata:", a.output.with_suffix(".manifest.json"))
        return
    if a.command == "demo":
        inp = Path("data/processed/synthetic_demo.csv")
        write_demo_panel(inp, seed=a.seed)
        manifest = analyse(inp, a.output, seed=a.seed)
        print(f"SYNTHETIC DEMO: {manifest['countries_ranked']} markets. Not empirical results. Saved to {a.output}")
        return
    if a.command == "analyze":
        codes = [i.code for i in INDICATORS]
        weights = dict(zip(codes, [a.weight_market_size, a.weight_growth, a.weight_governance,
                                   a.weight_logistics, a.weight_digital]))
        meta = analyse(a.input, a.output, missing_policy=a.missing_policy,
                       exclude_countries={c.upper() for c in a.exclude},
                       weights=weights, n_sim=a.simulations, seed=a.seed)
        print(f"{meta['data_kind']} | {meta['countries_ranked']} countries -> {a.output}")
        return

if __name__ == "__main__":
    main()
