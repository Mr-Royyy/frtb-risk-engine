# FRTB-Lite Market Risk Engine

A lightweight institutional-style **market-risk analytics and model-validation terminal** built with a C++20 quantitative core and a Python research/dashboard layer.

This project is inspired by Basel/FRTB market-risk concepts, but it is intentionally **not** a full regulatory capital implementation. The goal is to demonstrate practical market-risk engineering: portfolio ingestion, risk-factor mapping, VaR, Expected Shortfall, stress testing, backtesting, and clean internal-risk-dashboard reporting.

## Product vision

> Build a lightweight risk terminal that lets a user upload or construct a portfolio, calculate VaR / Expected Shortfall / stress losses, decompose risk by asset and factor, and validate the model through backtesting.

## What this starter repo includes

This ZIP is a clean starting point for VS Code and GitHub. It includes:

- C++20 risk-engine scaffolding with documented classes.
- Historical VaR and Expected Shortfall calculators.
- Stress testing and simple backtesting modules.
- Python data-validation and analytics scripts.
- Streamlit dashboard starter with institutional risk-terminal layout.
- Sample portfolio, factor mapping, stress scenarios, and price history.
- CMake build files, VS Code tasks, GitHub Actions CI, and setup documentation.

## MVP scope

The first version supports:

- Equities
- ETFs
- FX exposure
- Simple options as mapped exposures

The MVP risk outputs are:

- Portfolio market value
- Historical 1-day VaR
- Expected Shortfall
- Preset stress scenario losses
- Top risk contributors
- Basic backtesting exceptions

Advanced features such as full FRTB bucket rules, complete rates curve construction, credit default risk capital, exotic derivatives, and official regulatory capital reporting are intentionally out of scope.

## Repo structure

```text
frtb-lite-risk-engine/
  cpp/
    include/                # C++ public headers
    src/                    # C++ implementation files
    tests/                  # C++ unit-style tests
    CMakeLists.txt

  python/
    data/                   # Data schemas, loaders, validators
    analytics/              # Risk-run and backtesting scripts
    bindings/               # Optional pybind11 starter binding
    dashboard/              # Streamlit app and pages

  sample_data/              # Small realistic sample input files
  reports/                  # Methodology and validation report templates
  .vscode/                  # VS Code tasks/settings
  .github/workflows/        # CI starter
```

## Quick start: Python layer

From the project root:

```bash
python -m venv .venv
```

On Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
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

Run the first risk calculation:

```bash
python python/analytics/run_risk.py \
  --portfolio sample_data/sample_portfolio.csv \
  --prices sample_data/sample_prices.csv \
  --factors sample_data/factor_mapping.csv \
  --scenarios sample_data/stress_scenarios.yaml
```

Launch the dashboard:

```bash
streamlit run python/dashboard/app.py
```

## Quick start: C++ layer

From the project root:

```bash
cmake -S cpp -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

Run the demo executable:

```bash
./build/frtb_lite_demo
```

On Windows, the executable may be under:

```bash
build\Debug\frtb_lite_demo.exe
```

## Why this project is strong for quant/risk roles

This is not positioned as a basic stock-prediction project. It is structured like a small version of a real market-risk platform:

1. A portfolio is mapped to risk factors.
2. Risk is measured through VaR, Expected Shortfall, and stress loss.
3. Model reliability is tested through backtesting.
4. The dashboard explains drivers and exceptions.
5. The C++ core shows quant-engineering ability beyond notebooks.

## Suggested resume bullet

Built an FRTB-inspired C++/Python market-risk engine calculating VaR, Expected Shortfall, stress losses, and simplified delta/vega/curvature-style exposures across multi-asset portfolios, with model backtesting and a Streamlit risk dashboard.

## Important disclaimer

This project is educational and portfolio-focused. It is not financial advice, trading advice, or a complete Basel/FRTB regulatory capital calculator.
