# Project roadmap

## Milestone 1: Data contract and validation

Goal: define the exact input/output structure used by the risk engine.

Definition of done:

- `sample_portfolio.csv` is documented and validated.
- `factor_mapping.csv` maps each instrument to risk factors.
- `stress_scenarios.yaml` defines reusable stress shocks.
- Python validator rejects missing prices, duplicated IDs, unsupported assets, and unmapped tickers.

## Milestone 2: C++ risk core

Goal: build the core classes and calculation engines.

Definition of done:

- `Position` and `Portfolio` objects are implemented.
- Historical VaR and Expected Shortfall work from a P&L/loss vector.
- Stress testing can apply simple factor shocks.
- Unit tests pass through CMake/CTest.

## Milestone 3: Python analytics layer

Goal: make the C++ engine callable from Python and compare outputs.

Definition of done:

- Python can run portfolio validation and sample risk calculations.
- Sample risk outputs can be saved as CSV/JSON.
- Python baseline is available for comparison.

## Milestone 4: Dashboard MVP

Goal: make the project readable to a recruiter, risk analyst, or quant developer.

Definition of done:

- Streamlit dashboard loads the sample portfolio.
- Dashboard shows market value, VaR, ES, stress losses, and top contributors.
- Methodology page explains formulas and limitations.

## Milestone 5: FRTB-lite sensitivities

Goal: add simplified standardized-approach concepts.

Definition of done:

- Delta exposure is shown by bucket.
- Vega exposure is shown for options.
- Curvature-style up/down shock losses are estimated.
- Documentation clearly says this is simplified and not regulatory-complete.

## Milestone 6: Backtesting and model validation

Goal: show that the model is tested, not just calculated.

Definition of done:

- Rolling VaR forecasts are compared against realized next-day P&L.
- Exceptions and exception severity are reported.
- A validation report explains model weaknesses.

## Milestone 7: ML regime detection

Goal: use ML as a risk-management feature, not as price prediction.

Definition of done:

- Features include volatility, correlation, drawdown, and dispersion.
- Model classifies calm / normal / stressed regimes.
- Dashboard connects regimes to risk warnings and stress emphasis.
