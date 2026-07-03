# Model Validation Report

## Executive summary

This report should summarize whether the market-risk model appears reliable for the sample portfolio and where it fails.

## Model being validated

Model name: FRTB-Lite Historical Simulation VaR

Current model features:

- Historical 1-day VaR
- Expected Shortfall
- Scenario stress testing
- Simplified sensitivity outputs

## Backtesting approach

The validation workflow compares forecast VaR against realized next-day portfolio loss.

A VaR exception occurs when:

```text
realized_loss > forecast_var
```

## Validation metrics

To be completed after rolling backtest implementation:

| Metric | Value |
|---|---:|
| Observations | TBD |
| VaR confidence | TBD |
| Exceptions | TBD |
| Exception rate | TBD |
| Average exception severity | TBD |
| Worst exception | TBD |

## Known model risks

- Historical simulation may understate risk when the lookback window excludes crisis periods.
- Linear P&L approximation can miss nonlinear option exposure.
- Correlations can change during market stress.
- Data-quality issues can create false confidence.
- Simplified stress scenarios may not capture basis risk or liquidity risk.

## Validation conclusion

TBD after implementation of rolling VaR backtesting.
