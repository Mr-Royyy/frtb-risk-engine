"""
Streamlit dashboard for the FRTB-Lite Market Risk Engine.

The dashboard is designed to look like an internal market-risk terminal:
summary cards first, then loss distribution, stress scenarios, and methodology.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Make project root importable when running `streamlit run python/dashboard/app.py`.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from python.analytics.run_risk import (  # noqa: E402
    compute_es_contributions,
    compute_portfolio_pnl,
    compute_stress_detail,
    compute_stress_losses,
    expected_shortfall,
    historical_var,
    load_scenarios,
)

from python.analytics.frtb_sensitivities import (  # noqa: E402
    aggregate_by_bucket,
    compute_frtb_lite_sensitivities,
)
from python.data.load_prices import calculate_returns, load_price_history  # noqa: E402


st.set_page_config(
    page_title="FRTB-Lite Market Risk Engine",
    page_icon="📉",
    layout="wide",
)


@st.cache_data
def load_sample_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """Load sample data once for dashboard responsiveness."""
    portfolio = pd.read_csv(PROJECT_ROOT / "sample_data/sample_portfolio.csv")
    factors = pd.read_csv(PROJECT_ROOT / "sample_data/factor_mapping.csv")
    prices = load_price_history(PROJECT_ROOT / "sample_data/sample_prices.csv")
    scenarios = load_scenarios(PROJECT_ROOT / "sample_data/stress_scenarios.yaml")
    return portfolio, factors, prices, scenarios


def format_currency(value: float) -> str:
    """Format a number as a clean risk-dashboard currency string."""
    return f"${value:,.0f}"


portfolio, factors, prices, scenarios = load_sample_data()
returns = calculate_returns(prices)
pnl = compute_portfolio_pnl(portfolio, returns, factors)
losses = -pnl

market_value = float((portfolio["quantity"] * portfolio["price"]).sum())
var_99 = historical_var(losses, 0.99)
es_975 = expected_shortfall(losses, 0.975)
stress = compute_stress_losses(portfolio, factors, scenarios)
stress_detail = compute_stress_detail(portfolio, factors, scenarios)
es_contrib = compute_es_contributions(portfolio, returns, factors)

frtb_sensitivities = compute_frtb_lite_sensitivities(
    portfolio=portfolio,
    factors=factors,
    valuation_date="2026-07-03",
)
frtb_bucket_summary = aggregate_by_bucket(frtb_sensitivities)

worst_stress = float(stress["stress_loss"].max())
total_capital_style_charge = float(frtb_bucket_summary["capital_style_charge"].sum())
largest_frtb_bucket = str(frtb_bucket_summary.iloc[0]["bucket"])

st.title("FRTB-Lite Market Risk Engine")
st.caption(
    "A lightweight C++/Python market-risk and model-validation terminal. "
    "Educational FRTB-inspired project, not a full regulatory capital calculator."
)

card_1, card_2, card_3, card_4, card_5 = st.columns(5)
card_1.metric("Portfolio Market Value", format_currency(market_value))
card_2.metric("1-Day 99% VaR", format_currency(var_99))
card_3.metric("97.5% Expected Shortfall", format_currency(es_975))
card_4.metric("Worst Stress Loss", format_currency(worst_stress))
card_5.metric("FRTB-Lite Charge", format_currency(total_capital_style_charge))

tab_overview, tab_stress, tab_frtb, tab_backtest, tab_methodology = st.tabs(
    [
        "Portfolio Overview",
        "Stress Testing",
        "FRTB-Lite Sensitivities",
        "Backtesting",
        "Methodology",
    ]
)

with tab_overview:
    st.subheader("Portfolio risk overview")

    left, right = st.columns([1.3, 1])

    with left:
        loss_frame = pd.DataFrame({"loss": losses})
        fig = px.histogram(
            loss_frame,
            x="loss",
            nbins=40,
            title="Historical portfolio loss distribution",
        )
        fig.add_vline(x=var_99, annotation_text="99% VaR")
        fig.add_vline(x=es_975, annotation_text="97.5% ES")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        portfolio_view = portfolio.copy()
        portfolio_view["market_value"] = portfolio_view["quantity"] * portfolio_view["price"]
        portfolio_view = portfolio_view.sort_values("market_value", ascending=False)
        st.dataframe(
            portfolio_view[
                ["position_id", "asset_type", "ticker", "quantity", "price", "currency", "market_value"]
            ],
            use_container_width=True,
            hide_index=True,
        )

with tab_stress:
    st.subheader("Scenario stress testing")
    st.write(
        "Stress scenarios answer the practical risk question: "
        "**what hurts the portfolio the most?**"
    )

    fig = px.bar(
        stress,
        x="scenario",
        y="stress_loss",
        hover_data=["description"],
        title="Stress loss by scenario",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(stress, use_container_width=True, hide_index=True)

with tab_frtb:
    st.subheader("Simplified FRTB-lite sensitivities")
    st.write(
        "This tab calculates simplified delta, vega, and curvature-style exposures "
        "by position and bucket. It is inspired by standardized market-risk concepts, "
        "but it is not a full Basel/FRTB regulatory capital calculator."
    )

    kpi_1, kpi_2, kpi_3 = st.columns(3)
    kpi_1.metric("Capital-Style Charge", format_currency(total_capital_style_charge))
    kpi_2.metric("Largest Risk Bucket", largest_frtb_bucket)
    kpi_3.metric("Risk Buckets", f"{len(frtb_bucket_summary)}")

    left, right = st.columns([1.2, 1])

    with left:
        fig = px.bar(
            frtb_bucket_summary,
            x="bucket",
            y="capital_style_charge",
            title="Capital-style charge by FRTB-lite bucket",
            hover_data=[
                "market_value",
                "delta_exposure",
                "vega_exposure",
                "curvature_exposure",
            ],
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        charge_breakdown = frtb_bucket_summary[
            ["bucket", "weighted_delta", "weighted_vega", "weighted_curvature"]
        ].melt(
            id_vars="bucket",
            var_name="risk_component",
            value_name="weighted_charge",
        )

        fig = px.bar(
            charge_breakdown,
            x="bucket",
            y="weighted_charge",
            color="risk_component",
            title="Delta / vega / curvature-style charge split",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Bucket summary**")
    st.dataframe(
        frtb_bucket_summary[
            [
                "bucket",
                "positions",
                "market_value",
                "delta_exposure",
                "vega_exposure",
                "curvature_exposure",
                "weighted_delta",
                "weighted_vega",
                "weighted_curvature",
                "capital_style_charge",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("**Position-level sensitivities**")
    st.dataframe(
        frtb_sensitivities[
            [
                "position_id",
                "asset_type",
                "ticker",
                "bucket",
                "market_value",
                "delta",
                "vega",
                "delta_exposure",
                "vega_exposure",
                "curvature_exposure",
                "capital_style_charge",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.info(
        "Interpretation: delta exposure captures linear price sensitivity, "
        "vega exposure captures option sensitivity to implied volatility, and "
        "curvature exposure captures simplified nonlinear option loss under "
        "up/down shocks."
    )

with tab_backtest:
    st.subheader("Backtesting and validation")
    st.write(
        "Backtesting compares predicted VaR against realized P&L. "
        "This starter page displays the concept; the rolling implementation lives in "
        "`python/analytics/run_backtest.py`."
    )

    backtest_frame = pd.DataFrame({"pnl": pnl, "loss": losses})
    backtest_frame["static_var_99"] = var_99
    backtest_frame["exception"] = backtest_frame["loss"] > backtest_frame["static_var_99"]

    exception_count = int(backtest_frame["exception"].sum())
    exception_rate = exception_count / len(backtest_frame)

    col_a, col_b = st.columns(2)
    col_a.metric("Static VaR Exceptions", f"{exception_count}")
    col_b.metric("Exception Rate", f"{exception_rate:.2%}")

    fig = px.line(
        backtest_frame.reset_index(),
        x="date",
        y=["loss", "static_var_99"],
        title="Realized loss versus static 99% VaR threshold",
    )
    st.plotly_chart(fig, use_container_width=True)

with tab_methodology:
    st.subheader("Methodology and limitations")
    st.markdown(
        """
        **Historical VaR:** calculated from the empirical distribution of daily portfolio losses.

        **Expected Shortfall:** average loss beyond the selected VaR threshold.

        **Stress testing:** applies predefined factor shocks to mapped position exposures.

        **FRTB-lite sensitivities:** simplified delta, vega, and curvature-style outputs.
        These are educational approximations and not complete Basel calculations.

        **Main limitations:** no full regulatory bucket/correlation framework yet, no complete
        option repricing yet, and no rates/credit curve construction yet.
        """
    )
