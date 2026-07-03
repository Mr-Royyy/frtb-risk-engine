"""
Price-history loading utilities.

The starter project uses a simple wide CSV format:

    date,AAPL,MSFT,SPY,USDCAD,...

Each asset column is a price series. The analytics layer converts prices into
daily returns and maps those returns to portfolio positions.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_price_history(path: Path) -> pd.DataFrame:
    """
    Load and basic-clean a wide price-history CSV.

    Args:
        path: CSV with a `date` column and one column per ticker.

    Returns:
        DataFrame indexed by date with numeric price columns.
    """
    prices = pd.read_csv(path, parse_dates=["date"])
    prices = prices.sort_values("date").set_index("date")

    for column in prices.columns:
        prices[column] = pd.to_numeric(prices[column], errors="coerce")

    return prices


def calculate_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Convert prices into simple daily returns.

    Returns are used by the historical simulation VaR/ES baseline.
    """
    return prices.pct_change().dropna(how="all")
