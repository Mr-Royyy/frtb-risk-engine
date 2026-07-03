"""
Market regime detection module for the FRTB-Lite Market Risk Engine.

This module classifies the recent market environment as calm, normal, volatile,
or stressed using transparent risk features.

Features used:
1. Realized volatility
2. Average cross-asset correlation
3. Maximum drawdown
4. Return dispersion
5. Volatility-of-volatility

This is intentionally written as a transparent model first. In a production
risk system, this could later be replaced or supplemented by KMeans, HMMs,
Gaussian mixture models, or supervised crisis classifiers.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from python.data.load_prices import calculate_returns, load_price_history


def max_drawdown(index_series: pd.Series) -> float:
    """
    Calculate maximum drawdown for an index-level return series.

    The input should be a cumulative wealth/index series. The output is negative
    or zero. For example, -0.20 means a 20% drawdown from peak to trough.
    """
    running_peak = index_series.cummax()
    drawdown = index_series / running_peak - 1.0
    return float(drawdown.min())


def calculate_regime_features(
    returns: pd.DataFrame,
    window: int = 30,
) -> pd.DataFrame:
    """
    Calculate rolling market-regime features.

    The function creates an equal-weighted market proxy from the return matrix.
    This keeps the regime detector simple and independent of a specific index.
    """
    clean_returns = returns.select_dtypes(include=[np.number]).fillna(0.0)

    if clean_returns.empty:
        raise ValueError("returns must contain at least one numeric return column")

    market_return = clean_returns.mean(axis=1)
    wealth_index = (1.0 + market_return).cumprod()

    rolling_volatility = market_return.rolling(window).std() * np.sqrt(252)
    rolling_vol_of_vol = rolling_volatility.rolling(window).std()

    rolling_dispersion = clean_returns.rolling(window).std().mean(axis=1) * np.sqrt(252)

    rolling_correlation = []
    for index_position in range(len(clean_returns)):
        if index_position < window:
            rolling_correlation.append(np.nan)
            continue

        window_returns = clean_returns.iloc[index_position - window : index_position]
        corr_matrix = window_returns.corr().replace([np.inf, -np.inf], np.nan)

        if corr_matrix.shape[0] <= 1:
            rolling_correlation.append(0.0)
            continue

        upper_triangle = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        average_corr = upper_triangle.stack().mean()
        rolling_correlation.append(float(average_corr) if pd.notna(average_corr) else 0.0)

    rolling_drawdown = []
    for index_position in range(len(wealth_index)):
        if index_position < window:
            rolling_drawdown.append(np.nan)
            continue

        window_wealth = wealth_index.iloc[index_position - window : index_position]
        rolling_drawdown.append(max_drawdown(window_wealth))

    features = pd.DataFrame(
        {
            "date": clean_returns.index,
            "market_return": market_return.values,
            "realized_volatility": rolling_volatility.values,
            "avg_correlation": rolling_correlation,
            "max_drawdown": rolling_drawdown,
            "dispersion": rolling_dispersion.values,
            "vol_of_vol": rolling_vol_of_vol.values,
        }
    )

    features["date"] = pd.to_datetime(features["date"])
    return features.dropna().reset_index(drop=True)


def percentile_score(series: pd.Series, value: float, higher_is_riskier: bool = True) -> float:
    """
    Convert a feature value into a percentile-style risk score from 0 to 1.
    """
    clean = series.dropna()

    if clean.empty:
        return 0.0

    percentile = float((clean <= value).mean())

    if higher_is_riskier:
        return percentile

    return 1.0 - percentile


def classify_regime(features: pd.DataFrame) -> dict[str, Any]:
    """
    Classify the latest market regime from rolling features.

    The regime score is a weighted blend of several risk features. Higher values
    indicate a more stressed market environment.
    """
    if features.empty:
        raise ValueError("features must not be empty")

    latest = features.iloc[-1]

    volatility_score = percentile_score(
        features["realized_volatility"],
        float(latest["realized_volatility"]),
        higher_is_riskier=True,
    )
    correlation_score = percentile_score(
        features["avg_correlation"],
        float(latest["avg_correlation"]),
        higher_is_riskier=True,
    )
    drawdown_score = percentile_score(
        features["max_drawdown"],
        float(latest["max_drawdown"]),
        higher_is_riskier=False,
    )
    dispersion_score = percentile_score(
        features["dispersion"],
        float(latest["dispersion"]),
        higher_is_riskier=True,
    )
    vol_of_vol_score = percentile_score(
        features["vol_of_vol"],
        float(latest["vol_of_vol"]),
        higher_is_riskier=True,
    )

    regime_score = (
        0.30 * volatility_score
        + 0.20 * correlation_score
        + 0.25 * drawdown_score
        + 0.15 * dispersion_score
        + 0.10 * vol_of_vol_score
    )

    if regime_score >= 0.80:
        regime = "stressed"
        recommendation = (
            "Use stressed calibration, review VaR exceptions, and prioritize "
            "scenario analysis over normal-market assumptions."
        )
    elif regime_score >= 0.60:
        regime = "volatile"
        recommendation = (
            "Increase monitoring frequency and check whether risk limits are "
            "being driven by correlation or volatility."
        )
    elif regime_score >= 0.35:
        regime = "normal"
        recommendation = (
            "Standard daily risk monitoring is appropriate, but continue tracking "
            "drawdown and correlation changes."
        )
    else:
        regime = "calm"
        recommendation = (
            "Market conditions appear calm, but VaR may understate risk if the "
            "calibration window excludes stressed periods."
        )

    feature_scores = {
        "volatility_score": volatility_score,
        "correlation_score": correlation_score,
        "drawdown_score": drawdown_score,
        "dispersion_score": dispersion_score,
        "vol_of_vol_score": vol_of_vol_score,
    }

    return {
        "date": str(pd.Timestamp(latest["date"]).date()),
        "regime": regime,
        "regime_score": float(regime_score),
        "recommendation": recommendation,
        "latest_features": {
            "realized_volatility": float(latest["realized_volatility"]),
            "avg_correlation": float(latest["avg_correlation"]),
            "max_drawdown": float(latest["max_drawdown"]),
            "dispersion": float(latest["dispersion"]),
            "vol_of_vol": float(latest["vol_of_vol"]),
        },
        "feature_scores": feature_scores,
    }


def write_regime_outputs(
    output_dir: Path,
    features: pd.DataFrame,
    classification: dict[str, Any],
) -> None:
    """
    Write regime detection artifacts for the dashboard and reports.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    features.to_csv(output_dir / "regime_features.csv", index=False)

    with (output_dir / "regime_summary.json").open("w", encoding="utf-8") as file:
        json.dump(classification, file, indent=2)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run market regime detection.")
    parser.add_argument("--prices", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--window", type=int, default=30)
    return parser.parse_args()


def main() -> int:
    """CLI entry point."""
    args = parse_args()

    prices = load_price_history(args.prices)
    returns = calculate_returns(prices)

    features = calculate_regime_features(returns, window=args.window)
    classification = classify_regime(features)

    write_regime_outputs(args.output_dir, features, classification)

    print("FRTB-Lite Regime Detection")
    print("--------------------------")
    print(f"Date: {classification['date']}")
    print(f"Regime: {classification['regime'].upper()}")
    print(f"Regime score: {classification['regime_score']:.2f}")
    print(f"Recommendation: {classification['recommendation']}")
    print()
    print(f"Wrote regime outputs to: {args.output_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())