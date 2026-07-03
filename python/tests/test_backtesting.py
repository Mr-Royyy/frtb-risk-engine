"""Tests for the FRTB-Lite backtesting module."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from python.analytics.backtesting import (
    create_validation_report,
    kupiec_test,
    rolling_historical_var_backtest,
    summarize_backtest,
)
from python.data.load_prices import calculate_returns, load_price_history


def test_kupiec_test_returns_valid_probability() -> None:
    """Kupiec test should return a p-value between 0 and 1."""
    result = kupiec_test(
        exception_count=1,
        observation_count=100,
        confidence_level=0.99,
    )

    assert 0 <= result["p_value"] <= 1
    assert result["expected_exception_rate"] == 0.010000000000000009


def test_backtest_generates_var_forecasts() -> None:
    """Sample data should generate valid rolling VaR forecasts."""
    portfolio = pd.read_csv(PROJECT_ROOT / "sample_data/sample_portfolio.csv")
    factors = pd.read_csv(PROJECT_ROOT / "sample_data/factor_mapping.csv")
    prices = load_price_history(PROJECT_ROOT / "sample_data/sample_prices.csv")
    returns = calculate_returns(prices)

    backtest = rolling_historical_var_backtest(
        portfolio=portfolio,
        returns=returns,
        factors=factors,
        confidence_level=0.99,
        lookback_window=60,
        min_observations=30,
    )

    valid = backtest.dropna(subset=["var_forecast"])

    assert not valid.empty
    assert {"date", "realized_loss", "var_forecast", "exception"}.issubset(backtest.columns)


def test_backtest_summary_has_validation_status() -> None:
    """Backtest summary should produce a model-validation status."""
    portfolio = pd.read_csv(PROJECT_ROOT / "sample_data/sample_portfolio.csv")
    factors = pd.read_csv(PROJECT_ROOT / "sample_data/factor_mapping.csv")
    prices = load_price_history(PROJECT_ROOT / "sample_data/sample_prices.csv")
    returns = calculate_returns(prices)

    backtest = rolling_historical_var_backtest(
        portfolio=portfolio,
        returns=returns,
        factors=factors,
        confidence_level=0.99,
        lookback_window=60,
        min_observations=30,
    )

    summary = summarize_backtest(
        backtest=backtest,
        confidence_level=0.99,
        lookback_window=60,
    )

    assert summary["validation_status"] in {"green", "yellow", "red", "insufficient_data"}
    assert summary["observation_count"] > 0


def test_validation_report_contains_key_sections() -> None:
    """Generated Markdown report should contain model-validation sections."""
    portfolio = pd.read_csv(PROJECT_ROOT / "sample_data/sample_portfolio.csv")
    factors = pd.read_csv(PROJECT_ROOT / "sample_data/factor_mapping.csv")
    prices = load_price_history(PROJECT_ROOT / "sample_data/sample_prices.csv")
    returns = calculate_returns(prices)

    backtest = rolling_historical_var_backtest(
        portfolio=portfolio,
        returns=returns,
        factors=factors,
        confidence_level=0.99,
        lookback_window=60,
        min_observations=30,
    )

    summary = summarize_backtest(
        backtest=backtest,
        confidence_level=0.99,
        lookback_window=60,
    )

    report = create_validation_report(summary, backtest)

    assert "# Model Validation Report" in report
    assert "Kupiec" in report
    assert "Limitations" in report