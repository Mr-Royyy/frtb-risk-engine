# FRTB-Lite Market Risk Engine

A lightweight institutional-style **market-risk analytics and model-validation terminal** built with a C++20 quantitative core and a Python research/dashboard layer.

This project is inspired by Basel/FRTB market-risk concepts, but it is intentionally **not** a full regulatory capital implementation. The goal is to demonstrate practical market-risk engineering: portfolio ingestion, risk-factor mapping, VaR, Expected Shortfall, stress testing, FRTB-lite sensitivities, backtesting, market-regime detection, and clean internal-risk-dashboard reporting.

## Product vision

> Build a lightweight risk terminal that lets a user upload or construct a portfolio, calculate VaR / Expected Shortfall / stress losses, decompose risk by asset and factor, validate the model through backtesting, and explain the current market regime.

## What this repo includes

This repo is structured like a small market-risk platform, not a one-off notebook.

It includes:

- C++20 risk-engine modules with documented classes.
- Historical VaR and Expected Shortfall calculators.
- C++ Monte Carlo VaR / Expected Shortfall engine.
- C++ and Python Monte Carlo benchmark workflow.
- Stress testing and position-level stress drilldowns.
- Simplified FRTB-lite delta, vega, and curvature-style sensitivity engine.
- Rolling VaR backtesting and model-validation reporting.
- Kupiec unconditional coverage test for VaR exception analysis.
- Market-regime detection using volatility, correlation, drawdown, dispersion, and volatility-of-volatility.
- Python data-validation and analytics scripts.
- Streamlit dashboard with portfolio, stress, FRTB-lite, backtesting, regime, and methodology tabs.
- Sample portfolio, factor mapping, stress scenarios, and price history.
- CMake build files, VS Code settings, GitHub Actions CI starter, and setup documentation.

## MVP scope

The current version supports:

- Equities
- ETFs
- FX exposure
- Simple European-style options as mapped exposures

The current MVP risk outputs are:

- Portfolio market value
- Historical 1-day VaR
- Expected Shortfall
- Expected Shortfall contribution by position
- Preset stress scenario losses
- Position-level stress drilldowns
- Simplified FRTB-lite delta exposure
- Simplified option vega exposure
- Simplified curvature-style option exposure
- Bucket-level capital-style charge
- Rolling VaR backtesting
- VaR exception dates and severity
- Kupiec p-value and validation status
- Market-regime classification

Advanced features such as full FRTB bucket rules, complete rates curve construction, credit default risk capital, exotic derivatives, official regulatory capital reporting, and production model-governance workflows are intentionally out of scope.

## Repo structure

```text
frtb-lite-risk-engine/
  cpp/
    include/                # C++ public headers
    src/                    # C++ implementation files
    tests/                  # C++ unit-style tests
    tools/                  # C++ benchmark executables
    CMakeLists.txt

  python/
    data/                   # Data schemas, loaders, validators
    analytics/              # Risk, FRTB-lite, backtesting, benchmark, and regime scripts
    dashboard/              # Streamlit dashboard

  sample_data/              # Sample portfolio, factor mapping, prices, and scenarios
  scripts/                  # Project utility scripts and benchmark runner
  reports/                  # Methodology, validation, and benchmark reports
  .vscode/                  # VS Code tasks/settings
  .github/workflows/        # CI starter
```

## Quick start: Python layer

From the project root, create a virtual environment:

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Validate the sample portfolio:

```bash
python python/data/validate_portfolio.py \
  --portfolio sample_data/sample_portfolio.csv \
  --factors sample_data/factor_mapping.csv
```

Run the main risk calculation:

```bash
python python/analytics/run_risk.py \
  --portfolio sample_data/sample_portfolio.csv \
  --prices sample_data/sample_prices.csv \
  --factors sample_data/factor_mapping.csv \
  --scenarios sample_data/stress_scenarios.yaml
```

Run the FRTB-lite sensitivities module:

```bash
python python/analytics/frtb_sensitivities.py \
  --portfolio sample_data/sample_portfolio.csv \
  --factors sample_data/factor_mapping.csv \
  --output-dir outputs \
  --valuation-date 2026-07-03
```

Run the rolling VaR backtest:

```bash
python python/analytics/backtesting.py \
  --portfolio sample_data/sample_portfolio.csv \
  --prices sample_data/sample_prices.csv \
  --factors sample_data/factor_mapping.csv \
  --output-dir outputs
```

Run market-regime detection:

```bash
python python/analytics/regime_detection.py \
  --prices sample_data/sample_prices.csv \
  --output-dir outputs
```

Launch the dashboard:

```bash
python -m streamlit run python/dashboard/app.py
```

## Dashboard tabs

The Streamlit dashboard includes:

```text
Portfolio Overview
Stress Testing
FRTB-Lite Sensitivities
Backtesting
Regime Detection
Methodology
```

The dashboard is designed to feel like an internal risk terminal. It shows summary cards, loss distributions, stress scenario results, FRTB-lite bucket charges, backtesting exceptions, validation status, and market-regime drivers.

## Quick start: C++ layer

On Windows, use **Developer PowerShell for VS 2022** or make sure MSVC Build Tools and CMake are available in your PATH.

Build the C++ engine:

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

The project includes a C++ Monte Carlo VaR / Expected Shortfall benchmark and a Python/Numpy baseline benchmark.

Build the C++ engine first:

```powershell
cmake -S cpp -B cpp\build -G "Visual Studio 17 2022" -A x64
cmake --build cpp\build --config Release
```

Run the C++ benchmark:

```powershell
.\cpp\build\Release\monte_carlo_benchmark.exe
```

Run the Python/Numpy baseline:

```powershell
python python\analytics\monte_carlo_python_baseline.py
```

Generate the benchmark report:

```powershell
python scripts\run_benchmarks.py
```

The generated benchmark report is written to:

```text
reports/benchmark_results.md
```

The benchmark demonstrates that the project has a compiled C++ risk engine in addition to the Python analytics and Streamlit dashboard.

The Python/Numpy baseline may be faster than the current scalar C++ implementation because NumPy uses optimized compiled numerical routines internally. The goal of the benchmark is not to claim that this C++ implementation is always faster. The goal is to show that the C++ engine builds, runs, produces comparable VaR / Expected Shortfall outputs, and can be benchmarked independently.

Future optimization work could include:

- Avoiding per-path memory allocation in the C++ Monte Carlo loop.
- Using Eigen for matrix operations.
- Adding OpenMP parallel simulation.
- Exposing the C++ engine to Python through pybind11.
- Calling the C++ Monte Carlo engine directly from the Streamlit dashboard.

## Testing

Run all Python tests:

```powershell
python -m pytest python\tests -q
```

Run all C++ tests:

```powershell
ctest --test-dir cpp\build --output-on-failure -C Release
```

Current test coverage includes:

- FRTB-lite sensitivities
- Black-Scholes option Greeks
- Bucket-level sensitivity aggregation
- Rolling VaR backtesting
- Kupiec coverage testing
- Validation report generation
- Market-regime detection
- C++ risk-engine unit tests
- C++ Monte Carlo VaR / ES engine tests

## Model methodology

### Historical VaR

Historical VaR is calculated from the empirical distribution of daily portfolio losses. Positive values represent losses.

### Expected Shortfall

Expected Shortfall is calculated as the average loss beyond the selected VaR threshold. This is useful because it focuses on tail-loss severity rather than only the cutoff point.

### Stress testing

Stress testing applies predefined factor shocks to mapped position exposures. The stress engine supports portfolio-level and position-level stress loss outputs.

### FRTB-lite sensitivities

The FRTB-lite module calculates simplified:

- Delta exposure
- Vega exposure
- Curvature-style option exposure
- Bucket-level capital-style charges

This is inspired by standardized market-risk concepts, but it is not a full Basel/FRTB implementation.

### Backtesting

The backtesting module compares rolling historical VaR forecasts against realized portfolio losses. It tracks exception dates, exception severity, rolling exception rates, Kupiec p-values, and validation status.

### Regime detection

The regime detection module classifies the market environment as calm, normal, volatile, or stressed using:

- Realized volatility
- Average cross-asset correlation
- Maximum drawdown
- Return dispersion
- Volatility-of-volatility

The purpose is to connect market-regime awareness to risk monitoring and model validation.

## Why this project is strong for quant/risk roles

This is not positioned as a basic stock-prediction project. It is structured like a small version of a real market-risk platform.

The project shows:

1. A portfolio is mapped to risk factors.
2. Risk is measured through VaR, Expected Shortfall, and stress loss.
3. Simplified FRTB-style delta, vega, and curvature outputs are calculated.
4. Model reliability is tested through rolling VaR backtesting.
5. Exceptions are evaluated using Kupiec-style coverage testing.
6. Market regimes are classified using transparent risk features.
7. The dashboard explains drivers, losses, exceptions, and model limitations.
8. The C++ core shows quant-engineering ability beyond Python notebooks.
9. The benchmark workflow shows the compiled engine can be tested independently.

## Suggested resume bullets

Built an FRTB-inspired C++/Python market-risk engine calculating VaR, Expected Shortfall, stress losses, and simplified delta/vega/curvature-style sensitivities across multi-asset portfolios, with model backtesting, market-regime detection, and a Streamlit risk dashboard.

Implemented a C++ Monte Carlo VaR / Expected Shortfall engine with benchmark tooling against a Python/Numpy baseline, validating risk outputs through unit tests, generated reports, and a reproducible CMake build workflow.

Developed a model-validation layer with rolling historical VaR forecasts, realized P&L comparison, exception tracking, Kupiec coverage testing, and downloadable Markdown validation reports.

## Important disclaimer

This project is educational and portfolio-focused. It is not financial advice, trading advice, or a complete Basel/FRTB regulatory capital calculator.