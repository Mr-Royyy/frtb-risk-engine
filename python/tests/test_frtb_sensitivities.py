"""Tests for the simplified FRTB-lite sensitivity module."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from python.analytics.frtb_sensitivities import (
    aggregate_by_bucket,
    black_scholes_price_and_greeks,
    compute_frtb_lite_sensitivities,
)


def test_black_scholes_call_has_positive_delta_and_vega() -> None:
    """A normal call option should have positive delta and positive vega."""
    result = black_scholes_price_and_greeks(
        spot=100.0,
        strike=105.0,
        time_to_maturity=0.5,
        risk_free_rate=0.04,
        volatility=0.30,
        option_type="Call",
    )

    assert result["price"] > 0
    assert 0 < result["delta"] < 1
    assert result["vega"] > 0


def test_sample_portfolio_creates_frtb_lite_sensitivities() -> None:
    """The sample portfolio should produce position-level FRTB-lite outputs."""
    portfolio = pd.read_csv(PROJECT_ROOT / "sample_data/sample_portfolio.csv")
    factors = pd.read_csv(PROJECT_ROOT / "sample_data/factor_mapping.csv")

    sensitivities = compute_frtb_lite_sensitivities(
        portfolio=portfolio,
        factors=factors,
        valuation_date="2026-07-03",
    )

    required_columns = {
        "position_id",
        "ticker",
        "bucket",
        "delta_exposure",
        "vega_exposure",
        "curvature_exposure",
        "capital_style_charge",
    }

    assert required_columns.issubset(sensitivities.columns)
    assert len(sensitivities) == len(portfolio)
    assert sensitivities["capital_style_charge"].sum() > 0


def test_option_row_has_non_zero_vega_exposure() -> None:
    """The sample option should contribute vega exposure."""
    portfolio = pd.read_csv(PROJECT_ROOT / "sample_data/sample_portfolio.csv")
    factors = pd.read_csv(PROJECT_ROOT / "sample_data/factor_mapping.csv")

    sensitivities = compute_frtb_lite_sensitivities(
        portfolio=portfolio,
        factors=factors,
        valuation_date="2026-07-03",
    )

    option_rows = sensitivities[sensitivities["asset_type"] == "Option"]

    assert not option_rows.empty
    assert option_rows["vega_exposure"].abs().sum() > 0


def test_bucket_aggregation_includes_capital_style_charge() -> None:
    """Bucket aggregation should preserve a positive capital-style charge."""
    portfolio = pd.read_csv(PROJECT_ROOT / "sample_data/sample_portfolio.csv")
    factors = pd.read_csv(PROJECT_ROOT / "sample_data/factor_mapping.csv")

    sensitivities = compute_frtb_lite_sensitivities(
        portfolio=portfolio,
        factors=factors,
        valuation_date="2026-07-03",
    )

    bucket_summary = aggregate_by_bucket(sensitivities)

    assert "capital_style_charge" in bucket_summary.columns
    assert "US_EQ_TECH" in set(bucket_summary["bucket"])
    assert bucket_summary["capital_style_charge"].sum() > 0