# FRTB-Lite Market Risk Engine

A lightweight market-risk analytics and model-validation terminal built with a C++20 quantitative core and a Python analytics/dashboard layer.

The project is inspired by Basel/FRTB market-risk concepts, but it is not a full regulatory capital implementation. It focuses on practical market-risk workflows: portfolio ingestion, risk-factor mapping, VaR, Expected Shortfall, stress testing, simplified FRTB-style sensitivities, backtesting, regime detection, and dashboard reporting.

## Overview

The engine takes a sample multi-asset portfolio, maps each position to relevant risk factors, calculates portfolio risk measures, runs stress scenarios, validates VaR forecasts, and presents the results in a Streamlit dashboard.

The project is structured around three main areas:

- **Risk analytics:** VaR, Expected Shortfall, stress testing, risk contribution, and sensitivities.
- **Model validation:** rolling VaR backtesting, exception tracking, Kupiec coverage testing, and validation reports.
- **Quant engineering:** C++ risk engine, Python analytics layer, pybind11 bindings, tests, benchmarks, and CI.

## Current features

- Portfolio ingestion from CSV
- Risk-factor mapping
- Historical VaR
- Expected Shortfall
- Expected Shortfall contribution by position
- Preset stress scenario testing
- Position-level stress drilldowns
- Simplified FRTB-lite delta, vega, and curvature-style sensitivities
- Bucket-level capital-style charges
- Rolling VaR backtesting
- VaR exception tracking and severity analysis
- Kupiec unconditional coverage test
- Market-regime detection
- C++ Monte Carlo VaR / Expected Shortfall engine
- Python wrapper for the C++ engine through pybind11
- C++ and Python benchmark workflow
- Streamlit dashboard
- Python and C++ test suites
- GitHub Actions CI

## Supported sample instruments

The current sample portfolio includes:

- Equities
- ETFs
- FX exposure
- Simple European-style options

Option positions use a contract multiplier. For example:

```text
10 contracts × $8.20 premium × 100 multiplier = $8,200 market value
```

This keeps the sample portfolio closer to how listed equity options are normally represented.

## Repo structure

```text
frtb-lite-risk-engine/
  cpp/
    include/                # C++ headers
    src/                    # C++ source files
    tests/                  # C++ tests
    tools/                  # C++ benchmark executable
    bindings/               # pybind11 binding code
    CMakeLists.txt

  python/
    data/                   # Data loading and validation
    analytics/              # Risk, FRTB-lite, backtesting, regime, and benchmark scripts
    dashboard/              # Streamlit dashboard

  sample_data/              # Sample portfolio, prices, factor map, and stress scenarios
  scripts/                  # Utility scripts, including benchmark runner
  reports/                  # Generated reports
  .github/workflows/        # GitHub Actions CI
  .vscode/                  # VS Code settings
```

## Python setup

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Main Python workflows

Validate the sample portfolio:

```powershell
python python\data\validate_portfolio.py --portfolio sample_data\sample_portfolio.csv --factors sample_data\factor_mapping.csv
```

Run the main risk calculation:

```powershell
python python\analytics\run_risk.py --portfolio sample_data\sample_portfolio.csv --prices sample_data\sample_prices.csv --factors sample_data\factor_mapping.csv --scenarios sample_data\stress_scenarios.yaml
```

Run the FRTB-lite sensitivities module:

```powershell
python python\analytics\frtb_sensitivities.py --portfolio sample_data\sample_portfolio.csv --factors sample_data\factor_mapping.csv --output-dir outputs --valuation-date 2026-07-03
```

Run the rolling VaR backtest:

```powershell
python python\analytics\backtesting.py --portfolio sample_data\sample_portfolio.csv --prices sample_data\sample_prices.csv --factors sample_data\factor_mapping.csv --output-dir outputs
```

Run market-regime detection:

```powershell
python python\analytics\regime_detection.py --prices sample_data\sample_prices.csv --output-dir outputs
```

Run the C++ Monte Carlo engine from Python:

```powershell
python python\analytics\cpp_monte_carlo.py
```

Launch the dashboard:

```powershell
python -m streamlit run python\dashboard\app.py
```

## Dashboard

The Streamlit dashboard includes six tabs:

```text
Portfolio Overview
Stress Testing
FRTB-Lite Sensitivities
Backtesting
Regime Detection
Methodology
```

The dashboard shows portfolio market value, VaR, Expected Shortfall, worst stress loss, FRTB-lite charge, stress scenario losses, bucket-level sensitivities, VaR exceptions, validation status, regime signals, and methodology notes.

## C++ build

On Windows, use Developer PowerShell for VS 2022 or make sure MSVC Build Tools and CMake are available in the terminal.

Build the C++ project on Windows:

```powershell
cmake -S cpp -B cpp\build -G "Visual Studio 17 2022" -A x64
cmake --build cpp\build --config Release
```

Run C++ tests:

```powershell
ctest --test-dir cpp\build --output-on-failure -C Release
```

Run the C++ Monte Carlo benchmark:

```powershell
.\cpp\build\Release\monte_carlo_benchmark.exe
```

For Linux/macOS or CI-style builds:

```bash
cmake -S cpp -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

## Benchmarking

The benchmark workflow compares the C++ Monte Carlo VaR / Expected Shortfall engine with a Python/NumPy baseline.

Run the Python baseline:

```powershell
python python\analytics\monte_carlo_python_baseline.py
```

Generate the benchmark report:

```powershell
python scripts\run_benchmarks.py
```

The generated report is written to:

```text
reports/benchmark_results.md
```

The optimized C++ engine uses portfolio-variance compression for the linear-normal Monte Carlo case and partial selection for VaR / ES calculation. This avoids unnecessary full path construction and full sorting in the benchmark workflow.

Benchmark timings depend on the machine, compiler, build mode, and background processes, so the report should be read as a reproducible project benchmark rather than a universal performance claim.

## Testing

Run all Python tests:

```powershell
python -m pytest python\tests -q
```

Run all C++ tests:

```powershell
ctest --test-dir cpp\build --output-on-failure -C Release
```

The test suite covers:

- FRTB-lite sensitivities
- Black-Scholes option Greeks
- Bucket-level sensitivity aggregation
- Rolling VaR backtesting
- Kupiec coverage testing
- Validation report generation
- Market-regime detection
- C++ risk-engine logic
- C++ Monte Carlo VaR / ES engine
- pybind11 C++ binding from Python

## Methodology

### Historical VaR

Historical VaR is calculated from the empirical distribution of daily portfolio losses. Positive values represent losses.

### Expected Shortfall

Expected Shortfall is calculated as the average loss beyond the selected VaR threshold. This provides information about the severity of tail losses beyond the VaR cutoff.

### Stress testing

Stress testing applies predefined shocks to mapped risk factors. The project includes portfolio-level stress losses and position-level stress drilldowns.

### FRTB-lite sensitivities

The FRTB-lite module calculates simplified:

- Delta exposure
- Vega exposure
- Curvature-style option exposure
- Bucket-level capital-style charge

This is an educational approximation of standardized market-risk concepts. It does not reproduce the full Basel/FRTB rulebook.

### Backtesting

The backtesting module compares rolling 99% historical VaR forecasts against realized portfolio losses. It tracks exceptions, exception severity, rolling exception rates, Kupiec p-values, and validation status.

### Regime detection

The regime detection module classifies the market environment as calm, normal, volatile, or stressed using:

- Realized volatility
- Average cross-asset correlation
- Maximum drawdown
- Return dispersion
- Volatility-of-volatility

This connects market-regime monitoring with model validation and risk reporting.

## Generated outputs

The project can generate:

- Dashboard risk views
- Stress scenario results
- FRTB-lite bucket summaries
- Position-level sensitivity tables
- Backtesting results
- Model-validation report
- Regime detection output
- Benchmark report
- Python and C++ test results

## Example output

A sample run produces:

```text
Portfolio market value: 148,018.00
1-day 99% historical VaR: 2,632.28
1-day 97.5% Expected Shortfall: 2,388.27
```

The backtesting module produces a validation summary with the number of valid observations, VaR exceptions, observed exception rate, Kupiec p-value, and validation status.

The regime detection module returns the latest market regime label, regime score, and a short risk-monitoring interpretation.

## Project limitations

This is a simplified educational risk engine. It does not include:

- Full Basel/FRTB regulatory bucketing
- Complete prescribed risk weights and correlations
- Full rates curve construction
- Credit default risk capital
- Residual risk add-on
- Non-modellable risk factor treatment
- Trading desk approval workflow
- P&L attribution testing
- Production data governance controls
- Exotic derivatives or full option surface modelling

## Disclaimer

This project is educational and portfolio-focused. It is not financial advice, trading advice, or a complete Basel/FRTB regulatory capital calculator.
