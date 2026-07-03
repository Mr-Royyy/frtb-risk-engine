"""
Simplified FRTB-lite sensitivities module.

This file creates the first real standardized-approach-inspired layer of the
project. It is intentionally labelled "FRTB-lite" because it mirrors the risk
concepts used in market-risk frameworks without claiming to implement a full
Basel/FRTB regulatory capital engine.

The module calculates:
1. Delta exposure for linear products such as equities, ETFs, and FX.
2. Black-Scholes delta and vega for simple European options.
3. Curvature-style nonlinear exposure for options using up/down spot shocks.
4. Bucket-level aggregation by risk bucket from the factor-mapping file.
5. A simple capital-style charge using transparent educational risk weights.

Important limitation:
The output is useful for portfolio analytics and interviews, but it is not a
regulatory calculator. A production Basel/FRTB implementation would require the
full prescribed risk weights, buckets, correlations, liquidity horizons, legal
entity treatment, regulatory data controls, and model-governance workflow.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))


BUCKET_RISK_WEIGHTS: dict[str, dict[str, float]] = {
    "US_EQ_TECH": {"delta": 0.30, "vega": 0.21, "curvature": 1.00},
    "US_EQ_FIN": {"delta": 0.25, "vega": 0.21, "curvature": 1.00},
    "US_EQ_INDEX": {"delta": 0.20, "vega": 0.18, "curvature": 1.00},
    "CA_EQ_TECH": {"delta": 0.30, "vega": 0.21, "curvature": 1.00},
    "FX_USDCAD": {"delta": 0.15, "vega": 0.00, "curvature": 0.00},
    "DEFAULT": {"delta": 0.30, "vega": 0.21, "curvature": 1.00},
}


def normal_cdf(x: float) -> float:
    """Return the standard normal cumulative distribution function."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def normal_pdf(x: float) -> float:
    """Return the standard normal probability density function."""
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def years_to_maturity(maturity: Any, valuation_date: str | None = None) -> float:
    """
    Convert an option maturity date into years to maturity.

    If the maturity is missing or already expired, this function returns a small
    positive default. That keeps the starter project stable even when sample
    dates become stale over time.
    """
    if pd.isna(maturity) or str(maturity).strip() == "":
        return 0.50

    valuation = pd.Timestamp(valuation_date) if valuation_date else pd.Timestamp.today().normalize()
    expiry = pd.Timestamp(maturity)
    days = (expiry - valuation).days

    if days <= 0:
        return 0.50

    return max(days / 365.0, 1.0 / 365.0)


def black_scholes_price_and_greeks(
    spot: float,
    strike: float,
    time_to_maturity: float,
    risk_free_rate: float,
    volatility: float,
    option_type: str,
) -> dict[str, float]:
    """
    Price a simple European option and calculate delta/vega.

    Vega is per 1.00 volatility change. A 1 percentage-point volatility move is
    therefore vega * 0.01.
    """
    if spot <= 0 or strike <= 0 or time_to_maturity <= 0 or volatility <= 0:
        raise ValueError("spot, strike, time_to_maturity, and volatility must be positive")

    option_type_clean = option_type.strip().lower()
    sqrt_t = math.sqrt(time_to_maturity)

    d1 = (
        math.log(spot / strike)
        + (risk_free_rate + 0.5 * volatility * volatility) * time_to_maturity
    ) / (volatility * sqrt_t)
    d2 = d1 - volatility * sqrt_t

    discounted_strike = strike * math.exp(-risk_free_rate * time_to_maturity)

    if option_type_clean == "put":
        price = discounted_strike * normal_cdf(-d2) - spot * normal_cdf(-d1)
        delta = normal_cdf(d1) - 1.0
    else:
        price = spot * normal_cdf(d1) - discounted_strike * normal_cdf(d2)
        delta = normal_cdf(d1)

    vega = spot * normal_pdf(d1) * sqrt_t

    return {"price": price, "delta": delta, "vega": vega}


def infer_underlying_ticker(position: pd.Series, factors_by_ticker: pd.DataFrame) -> str:
    """
    Infer the underlying ticker for an option row.

    The sample factor map stores option exposure using a primary factor such as
    AAPL_RETURN. This function turns that back into AAPL.
    """
    ticker = str(position["ticker"])

    if ticker in factors_by_ticker.index:
        primary_factor = str(factors_by_ticker.loc[ticker, "primary_factor"])
        if primary_factor.endswith("_RETURN"):
            return primary_factor.replace("_RETURN", "")

    if "_CALL" in ticker:
        return ticker.split("_CALL")[0]
    if "_PUT" in ticker:
        return ticker.split("_PUT")[0]

    return ticker


def lookup_spot_price(
    position: pd.Series,
    portfolio_by_ticker: pd.DataFrame,
    factors_by_ticker: pd.DataFrame,
) -> float:
    """
    Find the underlying spot price used for option Greeks.

    For options, this uses the underlying equity price from the portfolio if it
    is available. Otherwise, it falls back to the option row's own price.
    """
    underlying = infer_underlying_ticker(position, factors_by_ticker)

    if underlying in portfolio_by_ticker.index:
        return float(portfolio_by_ticker.loc[underlying, "price"])

    return float(position["price"])


def bucket_weights(bucket: str) -> dict[str, float]:
    """Return educational risk weights for a bucket."""
    return BUCKET_RISK_WEIGHTS.get(bucket, BUCKET_RISK_WEIGHTS["DEFAULT"])


def compute_option_sensitivities(
    position: pd.Series,
    portfolio_by_ticker: pd.DataFrame,
    factors_by_ticker: pd.DataFrame,
    risk_free_rate: float,
    implied_volatility: float,
    equity_shock: float,
    option_multiplier: int,
    valuation_date: str | None,
) -> dict[str, float]:
    """
    Calculate delta, vega, and curvature-style exposure for one option.

    Curvature is estimated by repricing the option after an up and down shock,
    subtracting the linear delta effect, and taking the larger absolute nonlinear
    residual. This is a simplified approximation of nonlinear option risk.
    """
    spot = lookup_spot_price(position, portfolio_by_ticker, factors_by_ticker)
    strike = float(position["strike"])
    quantity = float(position["quantity"])
    maturity = years_to_maturity(position.get("maturity", ""), valuation_date)
    option_type = str(position.get("option_type", "Call") or "Call")

    base = black_scholes_price_and_greeks(
        spot=spot,
        strike=strike,
        time_to_maturity=maturity,
        risk_free_rate=risk_free_rate,
        volatility=implied_volatility,
        option_type=option_type,
    )

    up_spot = spot * (1.0 + equity_shock)
    down_spot = spot * (1.0 - equity_shock)

    up = black_scholes_price_and_greeks(
        spot=up_spot,
        strike=strike,
        time_to_maturity=maturity,
        risk_free_rate=risk_free_rate,
        volatility=implied_volatility,
        option_type=option_type,
    )

    down = black_scholes_price_and_greeks(
        spot=down_spot,
        strike=strike,
        time_to_maturity=maturity,
        risk_free_rate=risk_free_rate,
        volatility=implied_volatility,
        option_type=option_type,
    )

    delta_exposure = base["delta"] * spot * quantity * option_multiplier
    vega_exposure = base["vega"] * quantity * option_multiplier

    pnl_up = (up["price"] - base["price"]) * quantity * option_multiplier
    pnl_down = (down["price"] - base["price"]) * quantity * option_multiplier
    linear_up = base["delta"] * (up_spot - spot) * quantity * option_multiplier
    linear_down = base["delta"] * (down_spot - spot) * quantity * option_multiplier

    curvature_exposure = max(abs(pnl_up - linear_up), abs(pnl_down - linear_down))

    return {
        "underlying_spot": spot,
        "model_price": base["price"],
        "delta": base["delta"],
        "vega": base["vega"],
        "delta_exposure": delta_exposure,
        "vega_exposure": vega_exposure,
        "curvature_exposure": curvature_exposure,
    }


def compute_frtb_lite_sensitivities(
    portfolio: pd.DataFrame,
    factors: pd.DataFrame,
    risk_free_rate: float = 0.04,
    implied_volatility: float = 0.30,
    equity_shock: float = 0.15,
    option_multiplier: int = 100,
    valuation_date: str | None = None,
) -> pd.DataFrame:
    """
    Calculate position-level simplified FRTB-lite sensitivities.

    Linear instruments use market value as delta exposure. Options use
    Black-Scholes delta and vega. Every row is then mapped to an educational
    risk-weighted capital-style charge.
    """
    factors_by_ticker = factors.set_index("ticker").fillna("")
    portfolio_by_ticker = portfolio.set_index("ticker")
    rows: list[dict[str, Any]] = []

    for _, position in portfolio.iterrows():
        ticker = str(position["ticker"])
        asset_type = str(position["asset_type"])
        market_value = float(position["quantity"] * position["price"])

        if ticker in factors_by_ticker.index:
            bucket = str(factors_by_ticker.loc[ticker, "bucket"]).strip()
            if bucket == "" or bucket.lower() == "nan":
                bucket = f"FX_{ticker}" if asset_type.lower() == "fx" else "DEFAULT"

            primary_factor = str(factors_by_ticker.loc[ticker, "primary_factor"])
            vol_factor = str(factors_by_ticker.loc[ticker, "vol_factor"])
        else:
            bucket = "DEFAULT"
            primary_factor = ticker
            vol_factor = ""

        weights = bucket_weights(bucket)

        delta = 1.0
        vega = 0.0
        underlying_spot = float(position["price"])
        model_price = float(position["price"])
        delta_exposure = market_value
        vega_exposure = 0.0
        curvature_exposure = 0.0

        if asset_type.lower() == "option":
            option_result = compute_option_sensitivities(
                position=position,
                portfolio_by_ticker=portfolio_by_ticker,
                factors_by_ticker=factors_by_ticker,
                risk_free_rate=risk_free_rate,
                implied_volatility=implied_volatility,
                equity_shock=equity_shock,
                option_multiplier=option_multiplier,
                valuation_date=valuation_date,
            )

            delta = option_result["delta"]
            vega = option_result["vega"]
            underlying_spot = option_result["underlying_spot"]
            model_price = option_result["model_price"]
            delta_exposure = option_result["delta_exposure"]
            vega_exposure = option_result["vega_exposure"]
            curvature_exposure = option_result["curvature_exposure"]

        weighted_delta = abs(delta_exposure) * weights["delta"]
        weighted_vega = abs(vega_exposure) * weights["vega"] * 0.01
        weighted_curvature = abs(curvature_exposure) * weights["curvature"]
        capital_style_charge = weighted_delta + weighted_vega + weighted_curvature

        rows.append(
            {
                "position_id": position["position_id"],
                "asset_type": asset_type,
                "ticker": ticker,
                "bucket": bucket,
                "primary_factor": primary_factor,
                "vol_factor": vol_factor,
                "market_value": market_value,
                "underlying_spot": underlying_spot,
                "model_price": model_price,
                "delta": delta,
                "vega": vega,
                "delta_exposure": delta_exposure,
                "vega_exposure": vega_exposure,
                "curvature_exposure": curvature_exposure,
                "delta_risk_weight": weights["delta"],
                "vega_risk_weight": weights["vega"],
                "curvature_risk_weight": weights["curvature"],
                "weighted_delta": weighted_delta,
                "weighted_vega": weighted_vega,
                "weighted_curvature": weighted_curvature,
                "capital_style_charge": capital_style_charge,
            }
        )

    return pd.DataFrame(rows).sort_values("capital_style_charge", ascending=False)


def aggregate_by_bucket(sensitivities: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate position-level sensitivities into risk buckets.

    This deliberately uses a transparent sum-of-absolute-risk style. A full FRTB
    implementation would use prescribed within-bucket and cross-bucket
    correlations. That is outside the scope of the lite engine.
    """
    if sensitivities.empty:
        return pd.DataFrame()

    return (
        sensitivities.groupby("bucket", dropna=False)
        .agg(
            positions=("position_id", "count"),
            market_value=("market_value", "sum"),
            delta_exposure=("delta_exposure", "sum"),
            vega_exposure=("vega_exposure", "sum"),
            curvature_exposure=("curvature_exposure", "sum"),
            weighted_delta=("weighted_delta", "sum"),
            weighted_vega=("weighted_vega", "sum"),
            weighted_curvature=("weighted_curvature", "sum"),
            capital_style_charge=("capital_style_charge", "sum"),
        )
        .reset_index()
        .sort_values("capital_style_charge", ascending=False)
    )


def write_frtb_outputs(
    output_dir: Path,
    sensitivities: pd.DataFrame,
    bucket_summary: pd.DataFrame,
) -> None:
    """Write FRTB-lite outputs for dashboard and reporting workflows."""
    output_dir.mkdir(parents=True, exist_ok=True)

    sensitivities.to_csv(output_dir / "frtb_position_sensitivities.csv", index=False)
    bucket_summary.to_csv(output_dir / "frtb_bucket_summary.csv", index=False)

    summary = {
        "total_capital_style_charge": float(bucket_summary["capital_style_charge"].sum()),
        "largest_bucket": str(bucket_summary.iloc[0]["bucket"]) if not bucket_summary.empty else "n/a",
        "position_count": int(sensitivities.shape[0]),
        "bucket_count": int(bucket_summary.shape[0]),
    }

    with (output_dir / "frtb_summary.json").open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for standalone FRTB-lite sensitivity runs."""
    parser = argparse.ArgumentParser(description="Run simplified FRTB-lite sensitivities.")
    parser.add_argument("--portfolio", type=Path, required=True)
    parser.add_argument("--factors", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--risk-free-rate", type=float, default=0.04)
    parser.add_argument("--implied-volatility", type=float, default=0.30)
    parser.add_argument("--equity-shock", type=float, default=0.15)
    parser.add_argument("--option-multiplier", type=int, default=100)
    parser.add_argument("--valuation-date", type=str, default=None)
    return parser.parse_args()


def main() -> int:
    """CLI entry point."""
    args = parse_args()

    portfolio = pd.read_csv(args.portfolio)
    factors = pd.read_csv(args.factors)

    sensitivities = compute_frtb_lite_sensitivities(
        portfolio=portfolio,
        factors=factors,
        risk_free_rate=args.risk_free_rate,
        implied_volatility=args.implied_volatility,
        equity_shock=args.equity_shock,
        option_multiplier=args.option_multiplier,
        valuation_date=args.valuation_date,
    )

    bucket_summary = aggregate_by_bucket(sensitivities)
    write_frtb_outputs(args.output_dir, sensitivities, bucket_summary)

    print("FRTB-Lite Sensitivity Run")
    print("-------------------------")
    print(f"Positions: {len(sensitivities)}")
    print(f"Buckets: {len(bucket_summary)}")
    print(f"Total capital-style charge: {bucket_summary['capital_style_charge'].sum():,.2f}")
    print()
    print("Bucket summary")
    print(
        bucket_summary.to_string(
            index=False,
            formatters={"capital_style_charge": "{:,.2f}".format},
        )
    )
    print()
    print(f"Wrote FRTB-lite outputs to: {args.output_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())