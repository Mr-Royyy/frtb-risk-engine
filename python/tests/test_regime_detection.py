"""Tests for market regime detection."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from python.analytics.regime_detection import (
    calculate_regime_features,
    classify_regime,
    max_drawdown,
)
from python.data.load_prices import calculate_returns, load_price_history


def test_max_drawdown_is_negative_or_zero() -> None:
    """A drawdown should be less than or equal to zero."""
    series = pd.Series([100.0, 110.0, 90.0, 95.0, 120.0])
    result = max_drawdown(series)

    assert result <= 0
    assert round(result, 4) == round(90.0 / 110.0 - 1.0, 4)


def test_regime_features_are_created_from_sample_prices() -> None:
    """Sample prices should produce non-empty regime features."""
    prices = load_price_history(PROJECT_ROOT / "sample_data/sample_prices.csv")
    returns = calculate_returns(prices)

    features = calculate_regime_features(returns, window=30)

    required_columns = {
        "date",
        "market_return",
        "realized_volatility",
        "avg_correlation",
        "max_drawdown",
        "dispersion",
        "vol_of_vol",
    }

    assert not features.empty
    assert required_columns.issubset(features.columns)


def test_classification_returns_valid_regime() -> None:
    """Regime classifier should return one of the expected labels."""
    prices = load_price_history(PROJECT_ROOT / "sample_data/sample_prices.csv")
    returns = calculate_returns(prices)

    features = calculate_regime_features(returns, window=30)
    classification = classify_regime(features)

    assert classification["regime"] in {"calm", "normal", "volatile", "stressed"}
    assert 0 <= classification["regime_score"] <= 1
    assert "recommendation" in classification