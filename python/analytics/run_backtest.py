"""
Rolling VaR backtesting starter.

This module is intentionally simple but shows the validation workflow:
forecast VaR from a rolling historical window, compare it to next-day realized
loss, and count exceptions.
"""

from __future__ import annotations

import pandas as pd


def rolling_var_backtest(
    pnl: pd.Series,
    window: int = 100,
    confidence: float = 0.99,
) -> pd.DataFrame:
    """
    Compare rolling VaR forecasts against realized next-day losses.

    Args:
        pnl: Daily portfolio P&L series. Positive values are gains.
        window: Historical window length used for each forecast.
        confidence: VaR confidence level.

    Returns:
        DataFrame with realized losses, VaR forecasts, and exception flags.
    """
    losses = -pnl
    rows: list[dict[str, float | bool]] = []

    for end_idx in range(window, len(losses)):
        history = losses.iloc[end_idx - window : end_idx]
        realized_loss = float(losses.iloc[end_idx])
        var_forecast = float(history.quantile(confidence, interpolation="higher"))

        rows.append(
            {
                "date": losses.index[end_idx],
                "realized_loss": realized_loss,
                "var_forecast": var_forecast,
                "exception": realized_loss > var_forecast,
            }
        )

    return pd.DataFrame(rows)
