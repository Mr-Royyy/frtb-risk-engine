"""
Backtesting and model-validation module for the FRTB-Lite Market Risk Engine.

This module compares predicted VaR against realized next-day portfolio losses.
The purpose is to make the project feel like a real market-risk/model-validation
system rather than a one-off VaR calculator.

The module calculates:
1. Rolling historical VaR forecasts.
2. Realized next-day portfolio losses.
3. VaR exceptions, also called breaches.
4. Exception severity.
5. Kupiec unconditional coverage test.
6. A compact model-validation summary.
7. CSV/JSON/Markdown outputs for dashboard and reporting.

Important note:
This is an educational validation module. It is inspired by market-risk model
validation practice, but it is not a complete regulatory backtesting framework.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from python.analytics.run_risk import compute_portfolio_pnl
from python.data.load_prices import calculate_returns, load_price_history


def safe_log(value: float) -> float:
    """
    Return log(value) with protection against log(0).

    This is needed for likelihood calculations when the observed exception rate
    is very close to zero.
    """
    return math.log(max(value, 1e-12))


def chi_square_1df_survival(lr_statistic: float) -> float:
    """
    Return the survival probability for a chi-square variable with 1 degree of freedom.

    For 1 degree of freedom, the chi-square survival function can be written
    using the complementary error function. This avoids adding scipy as a
    dependency just for one statistical test.
    """
    if lr_statistic < 0:
        return 1.0

    return math.erfc(math.sqrt(lr_statistic / 2.0))


def kupiec_test(exception_count: int, observation_count: int, confidence_level: float) -> dict[str, float]:
    """
    Run Kupiec's unconditional coverage test.

    The test checks whether the observed exception rate is consistent with the
    expected exception rate implied by the VaR confidence level.

    Example:
    For 99% VaR, the expected exception rate is 1%. If the portfolio has far
    more exceptions than expected, the model may be underestimating risk.
    """
    if observation_count <= 0:
        return {
            "lr_uc": 0.0,
            "p_value": 1.0,
            "observed_exception_rate": 0.0,
            "expected_exception_rate": 1.0 - confidence_level,
        }

    expected_exception_rate = 1.0 - confidence_level
    observed_exception_rate = exception_count / observation_count

    x = exception_count
    n = observation_count
    p = expected_exception_rate
    phat = min(max(observed_exception_rate, 1e-12), 1.0 - 1e-12)

    restricted_log_likelihood = (n - x) * safe_log(1.0 - p) + x * safe_log(p)
    unrestricted_log_likelihood = (n - x) * safe_log(1.0 - phat) + x * safe_log(phat)

    lr_uc = -2.0 * (restricted_log_likelihood - unrestricted_log_likelihood)
    p_value = chi_square_1df_survival(lr_uc)

    return {
        "lr_uc": float(lr_uc),
        "p_value": float(p_value),
        "observed_exception_rate": float(observed_exception_rate),
        "expected_exception_rate": float(expected_exception_rate),
    }


def traffic_light_status(exception_count: int, observation_count: int, confidence_level: float, p_value: float) -> str:
    """
    Assign a simple model-validation status.

    This is not a formal Basel traffic-light implementation. It is a transparent
    project-friendly status label for the dashboard and Markdown report.
    """
    if observation_count <= 0:
        return "insufficient_data"

    expected_exceptions = observation_count * (1.0 - confidence_level)

    if p_value >= 0.05 and exception_count <= max(2.0 * expected_exceptions, expected_exceptions + 2):
        return "green"

    if p_value >= 0.01:
        return "yellow"

    return "red"


def rolling_historical_var_backtest(
    portfolio: pd.DataFrame,
    returns: pd.DataFrame,
    factors: pd.DataFrame,
    confidence_level: float = 0.99,
    lookback_window: int = 60,
    min_observations: int = 30,
) -> pd.DataFrame:
    """
    Create a rolling historical VaR backtest table.

    For each date, the model uses prior losses to estimate the VaR forecast.
    It then compares that forecast to the realized loss on the current date.
    This avoids look-ahead bias because today's realized loss is not used to
    forecast today's VaR.
    """
    if lookback_window < min_observations:
        raise ValueError("lookback_window must be greater than or equal to min_observations")

    pnl = compute_portfolio_pnl(portfolio, returns, factors)
    realized_losses = -pnl

    rows: list[dict[str, Any]] = []

    for index_position in range(len(realized_losses)):
        current_date = realized_losses.index[index_position]
        start_position = max(0, index_position - lookback_window)
        historical_window = realized_losses.iloc[start_position:index_position].dropna()

        if len(historical_window) < min_observations:
            var_forecast = np.nan
            exception = False
            exception_severity = 0.0
        else:
            var_forecast = float(np.quantile(historical_window, confidence_level, method="higher"))
            current_loss = float(realized_losses.iloc[index_position])
            exception = current_loss > var_forecast
            exception_severity = max(current_loss - var_forecast, 0.0)

        rows.append(
            {
                "date": current_date,
                "realized_pnl": float(pnl.iloc[index_position]),
                "realized_loss": float(realized_losses.iloc[index_position]),
                "var_forecast": var_forecast,
                "exception": bool(exception),
                "exception_severity": float(exception_severity),
            }
        )

    result = pd.DataFrame(rows)
    result["date"] = pd.to_datetime(result["date"])
    result["rolling_exception_count_20d"] = result["exception"].rolling(20, min_periods=1).sum()
    result["rolling_exception_rate_20d"] = result["exception"].rolling(20, min_periods=1).mean()

    return result


def summarize_backtest(
    backtest: pd.DataFrame,
    confidence_level: float = 0.99,
    lookback_window: int = 60,
) -> dict[str, Any]:
    """
    Create a compact validation summary from a backtest table.
    """
    valid = backtest.dropna(subset=["var_forecast"]).copy()

    observation_count = int(len(valid))
    exception_count = int(valid["exception"].sum())

    kupiec = kupiec_test(
        exception_count=exception_count,
        observation_count=observation_count,
        confidence_level=confidence_level,
    )

    average_var = float(valid["var_forecast"].mean()) if observation_count else 0.0
    average_realized_loss = float(valid["realized_loss"].mean()) if observation_count else 0.0
    worst_realized_loss = float(valid["realized_loss"].max()) if observation_count else 0.0
    max_exception_severity = float(valid["exception_severity"].max()) if observation_count else 0.0

    status = traffic_light_status(
        exception_count=exception_count,
        observation_count=observation_count,
        confidence_level=confidence_level,
        p_value=kupiec["p_value"],
    )

    return {
        "model": "Rolling Historical VaR",
        "confidence_level": confidence_level,
        "lookback_window": lookback_window,
        "observation_count": observation_count,
        "exception_count": exception_count,
        "expected_exception_rate": kupiec["expected_exception_rate"],
        "observed_exception_rate": kupiec["observed_exception_rate"],
        "kupiec_lr_uc": kupiec["lr_uc"],
        "kupiec_p_value": kupiec["p_value"],
        "validation_status": status,
        "average_var": average_var,
        "average_realized_loss": average_realized_loss,
        "worst_realized_loss": worst_realized_loss,
        "max_exception_severity": max_exception_severity,
    }

def dataframe_to_markdown_table(dataframe: pd.DataFrame) -> str:
    """
    Convert a DataFrame into a simple Markdown table without optional dependencies.

    Pandas' built-in DataFrame.to_markdown() requires the optional tabulate
    package. This project avoids that dependency so tests and CI stay lighter.
    """
    if dataframe.empty:
        return ""

    display_df = dataframe.copy()

    for column in display_df.columns:
        if pd.api.types.is_datetime64_any_dtype(display_df[column]):
            display_df[column] = display_df[column].dt.strftime("%Y-%m-%d")
        elif pd.api.types.is_float_dtype(display_df[column]):
            display_df[column] = display_df[column].map(lambda value: f"{value:,.2f}")

    headers = [str(column) for column in display_df.columns]
    separator = ["---"] * len(headers)

    rows = []
    rows.append("| " + " | ".join(headers) + " |")
    rows.append("| " + " | ".join(separator) + " |")

    for _, row in display_df.iterrows():
        row_values = [str(row[column]) for column in display_df.columns]
        rows.append("| " + " | ".join(row_values) + " |")

    return "\n".join(rows)

def create_validation_report(summary: dict[str, Any], backtest: pd.DataFrame) -> str:
    """
    Create a Markdown model-validation report.

    The report is intentionally written like a concise internal validation note:
    model, test window, exceptions, statistical result, interpretation, and
    limitations.
    """
    valid = backtest.dropna(subset=["var_forecast"]).copy()
    exceptions = valid[valid["exception"]].copy()

    if exceptions.empty:
        exception_table = "No VaR exceptions were observed in the valid backtest window."
    else:
        exception_table = dataframe_to_markdown_table(
            exceptions[["date", "realized_loss", "var_forecast", "exception_severity"]]
        )

    status = str(summary["validation_status"]).upper()

    if summary["validation_status"] == "green":
        interpretation = (
            "The observed exception frequency is broadly consistent with the "
            "selected VaR confidence level. The model is acceptable for this "
            "educational sample, while still requiring monitoring during stress."
        )
    elif summary["validation_status"] == "yellow":
        interpretation = (
            "The observed exception pattern is borderline. The model should be "
            "reviewed for stale calibration, missing risk factors, or clustering "
            "of losses during stressed periods."
        )
    elif summary["validation_status"] == "red":
        interpretation = (
            "The observed exception pattern is not consistent with the selected "
            "VaR confidence level. The model may be underestimating tail risk."
        )
    else:
        interpretation = (
            "There were not enough valid observations to form a reliable validation view."
        )

    return f"""# Model Validation Report

## Model tested

Rolling historical Value-at-Risk.

## Backtest setup

- Confidence level: {summary["confidence_level"]:.1%}
- Lookback window: {summary["lookback_window"]} trading days
- Valid backtest observations: {summary["observation_count"]}
- Expected exception rate: {summary["expected_exception_rate"]:.2%}

## Results

- VaR exceptions: {summary["exception_count"]}
- Observed exception rate: {summary["observed_exception_rate"]:.2%}
- Kupiec LR statistic: {summary["kupiec_lr_uc"]:.4f}
- Kupiec p-value: {summary["kupiec_p_value"]:.4f}
- Validation status: **{status}**
- Average VaR forecast: ${summary["average_var"]:,.2f}
- Worst realized loss: ${summary["worst_realized_loss"]:,.2f}
- Maximum exception severity: ${summary["max_exception_severity"]:,.2f}

## Interpretation

{interpretation}

## Exception details

{exception_table}

## Limitations

This validation report is generated from a simplified educational risk engine.
It does not include full trading-desk approval, P&L attribution, liquidity
horizons, non-modellable risk factor treatment, regulatory capital multipliers,
or complete FRTB governance requirements.

## Recommended next steps

1. Add a stressed calibration window.
2. Compare historical VaR against Monte Carlo VaR.
3. Track exceptions by market regime.
4. Add P&L attribution between clean P&L and risk-theoretical P&L.
"""


def write_backtest_outputs(
    output_dir: Path,
    backtest: pd.DataFrame,
    summary: dict[str, Any],
    report_text: str,
) -> None:
    """
    Write backtest artifacts for dashboard, reports, and GitHub review.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    backtest.to_csv(output_dir / "backtest_results.csv", index=False)

    with (output_dir / "backtest_summary.json").open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)

    report_path = output_dir / "model_validation_report.md"
    report_path.write_text(report_text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run rolling VaR backtesting.")
    parser.add_argument("--portfolio", type=Path, required=True)
    parser.add_argument("--prices", type=Path, required=True)
    parser.add_argument("--factors", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--confidence-level", type=float, default=0.99)
    parser.add_argument("--lookback-window", type=int, default=60)
    parser.add_argument("--min-observations", type=int, default=30)
    return parser.parse_args()


def main() -> int:
    """CLI entry point for the backtesting workflow."""
    args = parse_args()

    portfolio = pd.read_csv(args.portfolio)
    factors = pd.read_csv(args.factors)
    prices = load_price_history(args.prices)
    returns = calculate_returns(prices)

    backtest = rolling_historical_var_backtest(
        portfolio=portfolio,
        returns=returns,
        factors=factors,
        confidence_level=args.confidence_level,
        lookback_window=args.lookback_window,
        min_observations=args.min_observations,
    )

    summary = summarize_backtest(
        backtest=backtest,
        confidence_level=args.confidence_level,
        lookback_window=args.lookback_window,
    )

    report_text = create_validation_report(summary, backtest)

    write_backtest_outputs(
        output_dir=args.output_dir,
        backtest=backtest,
        summary=summary,
        report_text=report_text,
    )

    print("FRTB-Lite Backtesting Run")
    print("-------------------------")
    print(f"Model: {summary['model']}")
    print(f"Confidence level: {summary['confidence_level']:.1%}")
    print(f"Valid observations: {summary['observation_count']}")
    print(f"Exceptions: {summary['exception_count']}")
    print(f"Observed exception rate: {summary['observed_exception_rate']:.2%}")
    print(f"Kupiec p-value: {summary['kupiec_p_value']:.4f}")
    print(f"Validation status: {summary['validation_status'].upper()}")
    print()
    print(f"Wrote backtest outputs to: {args.output_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())