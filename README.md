# FRTB-Lite Market Risk Engine

I built this project as a lightweight market-risk engine and dashboard inspired by FRTB/Basel market-risk concepts. It is not meant to be a full regulatory capital calculator. The goal was to build something that feels closer to a real internal risk tool instead of a simple VaR notebook or stock prediction project.

The project takes a sample portfolio, maps positions to risk factors, calculates VaR and Expected Shortfall, runs stress scenarios, breaks down risk by bucket and position, backtests the model, and shows the results in a Streamlit dashboard.

## What I built

The main idea is a small market-risk terminal with two layers:

- A C++20 risk engine for performance-focused quantitative calculations.
- A Python layer for data loading, analytics, reporting, testing, and the dashboard.

The project currently includes:

- Portfolio ingestion from CSV
- Risk-factor mapping
- Historical VaR
- Expected Shortfall
- Expected Shortfall contribution by position
- Stress scenario testing
- Position-level stress drilldowns
- Simplified FRTB-lite delta, vega, and curvature-style sensitivities
- Bucket-level capital-style charges
- Rolling VaR backtesting
- Kupiec coverage testing
- Market-regime detection
- C++ Monte Carlo VaR / Expected Shortfall engine
- Python bindings for the C++ engine using pybind11
- C++ and Python benchmark workflow
- Streamlit dashboard
- Python and C++ tests
- GitHub Actions CI

## Why I made it

A lot of finance projects are based around predicting stock prices. I wanted to build something more related to risk, quant development, and model validation.

The project is meant to show that I can:

- Work with market-risk concepts like VaR, ES, stress testing, and backtesting.
- Build a C++ quantitative engine instead of only using Python notebooks.
- Connect C++ to Python using pybind11.
- Build a dashboard that explains the risk outputs clearly.
- Write tests and benchmark the engine.
- Document the assumptions and limitations of the model.

## Current scope

The sample portfolio supports:

- Equities
- ETFs
- FX exposure
- Simple European-style options

The option rows use a contract multiplier, so an option position like:

```text
10 contracts × $8.20 premium × 100 multiplier = $8,200 market value
```

is treated more realistically in the portfolio market value.

The project intentionally does not include full FRTB regulatory bucketing, complete rates curve construction, credit default risk capital, exotic derivatives, securitizations, or production model-governance workflows.

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

From the project root:

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

## Running the main Python workflows

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

The dashboard has these tabs:

```text
Portfolio Overview
Stress Testing
FRTB-Lite Sensitivities
Backtesting
Regime Detection
Methodology
```

The dashboard shows the main risk story of the portfolio: total market value, VaR, Expected Shortfall, worst stress loss, FRTB-lite charge, stress scenario losses, sensitivity buckets, VaR exceptions, validation status, and market-regime signals.

## C++ setup

On Windows, I used MSVC Build Tools, CMake, and Developer PowerShell for VS 2022.

Build the C++ project:

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

## Benchmarking

I added a benchmark workflow to compare the C++ Monte Carlo VaR / Expected Shortfall engine with a Python/NumPy baseline.

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

In my local benchmark, the optimized C++ Monte Carlo engine ran faster than the Python/NumPy baseline while producing comparable VaR and Expected Shortfall numbers.

The C++ engine was optimized by compressing the linear-normal portfolio into a portfolio-level variance and using partial selection for VaR / ES calculation instead of doing unnecessary full sorting.

## Testing

Run all Python tests:

```powershell
python -m pytest python\tests -q
```

Run all C++ tests:

```powershell
ctest --test-dir cpp\build --output-on-failure -C Release
```

The tests cover:

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

Expected Shortfall is calculated as the average loss beyond the selected VaR threshold. This gives more information about tail-loss severity than VaR alone.

### Stress testing

Stress scenarios apply predefined shocks to mapped risk factors. The output shows both total stress loss and position-level stress detail.

### FRTB-lite sensitivities

The FRTB-lite module calculates simplified:

- Delta exposure
- Vega exposure
- Curvature-style option exposure
- Bucket-level capital-style charge

This is only an educational approximation of standardized market-risk concepts. It is not a full Basel/FRTB implementation.

### Backtesting

The backtesting module compares rolling 99% historical VaR forecasts against realized portfolio losses. It tracks exceptions, exception severity, rolling exception rates, Kupiec p-values, and validation status.

### Regime detection

The regime detection module classifies the market environment as calm, normal, volatile, or stressed using:

- Realized volatility
- Average cross-asset correlation
- Maximum drawdown
- Return dispersion
- Volatility-of-volatility

The goal is to connect market-regime awareness to model validation and risk monitoring.

## Main outputs

The project generates:

- Dashboard risk views
- Stress scenario results
- FRTB-lite bucket summaries
- Position-level sensitivity tables
- Backtesting results
- Model-validation report
- Regime detection output
- Benchmark report
- C++ and Python test results

## What I learned

This project helped me learn how to connect finance concepts with software engineering. I worked through portfolio data design, risk-factor mapping, VaR/ES calculations, stress testing, option sensitivity logic, model backtesting, C++ performance work, pybind11 bindings, Streamlit dashboard design, CMake builds, CI issues, and benchmark reporting.

It also helped me understand how to explain model limitations. The project produces useful risk analytics, but it is still a simplified educational engine, not a production risk system.

## Resume bullets

Built an FRTB-inspired C++/Python market-risk engine calculating VaR, Expected Shortfall, stress losses, and simplified delta/vega/curvature-style sensitivities across multi-asset portfolios, with model backtesting, market-regime detection, and a Streamlit risk dashboard.

Implemented a C++ Monte Carlo VaR / Expected Shortfall engine with pybind11 bindings and benchmark tooling against a Python/NumPy baseline, optimizing the calculation path and validating outputs through C++ and Python tests.

Developed a model-validation layer with rolling historical VaR forecasts, realized P&L comparison, exception tracking, Kupiec coverage testing, and generated Markdown validation reports.

## Disclaimer

This project is educational and portfolio-focused. It is not financial advice, trading advice, or a complete Basel/FRTB regulatory capital calculator.
