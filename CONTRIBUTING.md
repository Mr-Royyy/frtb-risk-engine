# Contributing notes

This repo is meant to look like a serious portfolio project. Keep changes small, tested, and documented.

## Code style

- C++ code should use clear names, comments on financial assumptions, and simple module boundaries.
- Python code should use type hints, docstrings, and explicit error handling.
- Every risk formula should have a methodology note.

## Pull request checklist

Before committing:

```bash
python python/data/validate_portfolio.py --portfolio sample_data/sample_portfolio.csv --factors sample_data/factor_mapping.csv
python python/analytics/run_risk.py --portfolio sample_data/sample_portfolio.csv --prices sample_data/sample_prices.csv --factors sample_data/factor_mapping.csv --scenarios sample_data/stress_scenarios.yaml
cmake -S cpp -B build
cmake --build build
ctest --test-dir build --output-on-failure
```
