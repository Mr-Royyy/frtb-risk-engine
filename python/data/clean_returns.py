"""
Return-series cleaning helpers.

The first MVP keeps cleaning rules straightforward. Later versions can add
winsorization policies, stale-price detection, holiday calendars, and liquidity
filters.
"""

from __future__ import annotations

import pandas as pd


def clean_returns(returns: pd.DataFrame, max_abs_return: float = 0.50) -> pd.DataFrame:
    """
    Clean daily returns using simple sanity checks.

    Args:
        returns: Wide return matrix.
        max_abs_return: Returns larger than this absolute value are treated as bad data.

    Returns:
        Cleaned return matrix with extreme values set to missing and then dropped.
    """
    cleaned = returns.copy()
    cleaned = cleaned.mask(cleaned.abs() > max_abs_return)
    cleaned = cleaned.dropna(how="any")
    return cleaned
