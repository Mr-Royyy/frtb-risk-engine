"""
Run the first Python risk calculation for the FRTB-Lite engine.

This script is intentionally transparent. It gives you a working baseline before
the full C++ engine is connected through pybind11.

The method:
1. Load portfolio and price history.
2. Convert prices to returns.
3. Estimate daily position P&L using mapped ticker returns.
4. Convert P&L to losses.
5. Calculate historical VaR and Expected Shortfall.
6. Apply stress scenarios from YAML.
7. Print a compact risk report.

Example:
    python python/analytics/run_risk.py \
      --portfolio sample_data/sample_portfolio.csv \
      --prices sample_data/sample_prices.csv \
      --factors sample_data/factor_mapping.csv \
      --scenarios sample_data/stress_scenarios.yaml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

# Make the project root importable when this file is run directly from the repo root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from python.data.load_prices import calculate_returns, load_price_history


def historical_var(losses: pd.Series, confidence: float = 0.99) -> float:
    """
    Calculate historical Value-at-Risk from a positive-loss series.

    Positive values represent losses. At 99% confidence, VaR is the empirical
    99th percentile of the loss distribution.
    """
    return float(np.quantile(losses, confidence, method="higher"))


def expected_shortfall(losses: pd.Series, confidence: float = 0.975) -> float:
    """
    Calculate Expected Shortfall as average loss beyond the VaR threshold.
    """
    var_threshold = historical_var(losses, confidence)
    tail_losses = losses[losses >= var_threshold]
    if tail_losses.empty:
        return var_threshold
    return float(tail_losses.mean())


def load_scenarios(path: Path) -> dict[str, Any]:
    """Load stress scenarios from YAML."""
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)["scenarios"]


def position_market_values(portfolio: pd.DataFrame) -> pd.Series:
    """Return market value by ticker using quantity * price."""
    portfolio = portfolio.copy()
    portfolio["market_value"] = portfolio["quantity"] * portfolio["price"]
    return portfolio.groupby("ticker")["market_value"].sum()


def compute_portfolio_pnl(
    portfolio: pd.DataFrame,
    returns: pd.DataFrame,
    factors: pd.DataFrame,
) -> pd.Series:
    """
    Compute a simple historical P&L vector from direct ticker returns.

    For the MVP, each position is primarily driven by its own ticker when that
    ticker exists in the price matrix. For an option ticker, this starter maps
    the option to the underlying factor by stripping the sample naming pattern.
    Future work should replace this with full option repricing.
    """
    factors_by_ticker = factors.set_index("ticker")
    pnl = pd.Series(0.0, index=returns.index)

    for _, row in portfolio.iterrows():
        ticker = row["ticker"]
        market_value = float(row["quantity"] * row["price"])

        if ticker in returns.columns:
            risk_column = ticker
        elif ticker in factors_by_ticker.index:
            primary_factor = str(factors_by_ticker.loc[ticker, "primary_factor"])
            risk_column = primary_factor.replace("_RETURN", "")
        else:
            continue

        if risk_column not in returns.columns:
            continue

        # Linear P&L approximation: position market value multiplied by historical return.
        pnl += market_value * returns[risk_column].fillna(0.0)

    return pnl


def compute_stress_losses(
    portfolio: pd.DataFrame,
    factors: pd.DataFrame,
    scenarios: dict[str, Any],
) -> pd.DataFrame:
    """
    Apply simplified factor shocks and return scenario-level losses.

    The logic mirrors the C++ starter StressEngine:
    - primary factor has full weight
    - secondary factor has half weight
    - currency factor has full weight
    - option volatility factor adds a small vega proxy
    """
    factor_map = factors.set_index("ticker").fillna("")
    rows: list[dict[str, Any]] = []

    for scenario_name, scenario in scenarios.items():
        shocks = scenario.get("shocks", {})
        total_loss = 0.0

        for _, position in portfolio.iterrows():
            ticker = position["ticker"]
            market_value = float(position["quantity"] * position["price"])

            if ticker not in factor_map.index:
                continue

            mapping = factor_map.loc[ticker]

            primary = shocks.get(mapping["primary_factor"], 0.0)
            secondary = 0.5 * shocks.get(mapping["secondary_factor"], 0.0)
            currency = shocks.get(mapping["currency_factor"], 0.0)
            vol = shocks.get(mapping["vol_factor"], 0.0)

            combined_shock = primary + secondary + currency
            stressed_loss = -market_value * combined_shock

            if position["asset_type"] == "Option":
                stressed_loss += abs(market_value) * 0.10 * abs(vol)

            total_loss += stressed_loss

        rows.append(
            {
                "scenario": scenario_name,
                "description": scenario.get("description", ""),
                "stress_loss": total_loss,
            }
        )

    return pd.DataFrame(rows).sort_values("stress_loss", ascending=False)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run a sample FRTB-lite risk calculation.")
    parser.add_argument("--portfolio", type=Path, required=True)
    parser.add_argument("--prices", type=Path, required=True)
    parser.add_argument("--factors", type=Path, required=True)
    parser.add_argument("--scenarios", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    """CLI entry point."""
    args = parse_args()

    portfolio = pd.read_csv(args.portfolio)
    factors = pd.read_csv(args.factors)
    prices = load_price_history(args.prices)
    returns = calculate_returns(prices)
    scenarios = load_scenarios(args.scenarios)

    pnl = compute_portfolio_pnl(portfolio, returns, factors)
    losses = -pnl

    var_99 = historical_var(losses, confidence=0.99)
    es_975 = expected_shortfall(losses, confidence=0.975)
    market_value = float((portfolio["quantity"] * portfolio["price"]).sum())
    stress = compute_stress_losses(portfolio, factors, scenarios)

    print("FRTB-Lite Risk Run")
    print("------------------")
    print(f"Portfolio market value: {market_value:,.2f}")
    print(f"1-day 99% historical VaR: {var_99:,.2f}")
    print(f"1-day 97.5% Expected Shortfall: {es_975:,.2f}")
    print()
    print("Stress scenarios")
    print(stress.to_string(index=False, formatters={"stress_loss": "{:,.2f}".format}))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
