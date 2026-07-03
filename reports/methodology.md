# Methodology

## Purpose

This project is an educational FRTB-inspired market-risk engine. It is designed to show how a portfolio can be mapped to market risk factors, measured through VaR and Expected Shortfall, stressed under market scenarios, and validated through backtesting.

It is not a full Basel/FRTB regulatory calculator.

## Historical simulation VaR

The starter VaR method uses historical simulation.

Steps:

1. Load historical prices.
2. Convert prices into simple daily returns.
3. Estimate daily portfolio P&L from position market values and mapped returns.
4. Convert P&L into losses.
5. Calculate the empirical loss percentile at the selected confidence level.

## Expected Shortfall

Expected Shortfall is calculated as the average loss beyond the VaR threshold.

This is useful because VaR tells you where the tail begins, while Expected Shortfall tells you how severe losses are inside the tail.

## Stress testing

Stress testing applies named scenarios to mapped risk factors.

Example scenario shocks:

- Equity market crash
- Technology sector underperformance
- Volatility spike
- FX shock
- Macro rates/inflation shock

The output should show total stress loss and eventually position-level, bucket-level, and factor-level loss contributions.

## FRTB-lite sensitivity layer

The FRTB-lite module is planned as a simplified standardized-approach-inspired layer.

Initial simplified outputs:

- Delta exposure by bucket
- Vega proxy for options
- Curvature proxy for nonlinear option exposure

Future improvements:

- Black-Scholes option repricing
- True option Greeks
- Risk weights
- Bucket-level aggregation
- Cross-bucket correlation assumptions

## Model limitations

The starter version makes simplifying assumptions:

- Returns are calculated from adjusted sample price history.
- Position P&L is approximated linearly.
- Options are not fully repriced yet.
- FX conversion is simplified.
- Stress shocks are illustrative.
- FRTB outputs are educational approximations.

## Validation plan

The validation module should compare forecast VaR against next-day realized P&L.

Validation outputs should include:

- Exception count
- Exception rate
- Exception dates
- Exception severity
- Rolling breach chart
- Model comparison across historical, parametric, and Monte Carlo VaR
