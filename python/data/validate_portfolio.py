"""
Validate a portfolio file before it is sent into the risk engine.

Why this matters:
A real market-risk process should not silently accept broken data. Missing
prices, duplicated IDs, unmapped risk factors, or incomplete option fields can
produce risk numbers that look precise but are not reliable.

Example:
    python python/data/validate_portfolio.py \
        --portfolio sample_data/sample_portfolio.csv \
        --factors sample_data/factor_mapping.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

try:
    from portfolio_schema import (
        OPTION_REQUIRED_COLUMNS,
        REQUIRED_FACTOR_COLUMNS,
        REQUIRED_PORTFOLIO_COLUMNS,
        SUPPORTED_ASSET_TYPES,
        ValidationIssue,
        ValidationReport,
    )
except ImportError:  # Allows module import when called from project root.
    from python.data.portfolio_schema import (
        OPTION_REQUIRED_COLUMNS,
        REQUIRED_FACTOR_COLUMNS,
        REQUIRED_PORTFOLIO_COLUMNS,
        SUPPORTED_ASSET_TYPES,
        ValidationIssue,
        ValidationReport,
    )


def _missing_columns(frame: pd.DataFrame, required_columns: list[str]) -> list[str]:
    """Return required columns that are absent from a dataframe."""
    return [column for column in required_columns if column not in frame.columns]


def validate_portfolio(portfolio_path: Path, factor_path: Path) -> ValidationReport:
    """
    Validate portfolio and factor mapping input files.

    Args:
        portfolio_path: CSV file containing positions.
        factor_path: CSV file containing ticker-to-risk-factor mappings.

    Returns:
        ValidationReport with data-quality issues and pass/fail status.
    """
    issues: list[ValidationIssue] = []

    portfolio = pd.read_csv(portfolio_path)
    factors = pd.read_csv(factor_path)

    missing_portfolio_cols = _missing_columns(portfolio, REQUIRED_PORTFOLIO_COLUMNS)
    if missing_portfolio_cols:
        issues.append(
            ValidationIssue(
                "ERROR",
                "missing_portfolio_columns",
                f"Missing portfolio columns: {missing_portfolio_cols}",
            )
        )

    missing_factor_cols = _missing_columns(factors, REQUIRED_FACTOR_COLUMNS)
    if missing_factor_cols:
        issues.append(
            ValidationIssue(
                "ERROR",
                "missing_factor_columns",
                f"Missing factor mapping columns: {missing_factor_cols}",
            )
        )

    # If required columns are missing, avoid follow-on errors from column access.
    if issues:
        return ValidationReport(rows_loaded=len(portfolio), issues=issues)

    duplicate_ids = portfolio["position_id"].duplicated().sum()
    if duplicate_ids:
        issues.append(
            ValidationIssue(
                "ERROR",
                "duplicate_position_ids",
                f"Found {duplicate_ids} duplicate position_id values.",
            )
        )

    missing_tickers = portfolio["ticker"].isna().sum()
    if missing_tickers:
        issues.append(
            ValidationIssue("ERROR", "missing_tickers", f"Found {missing_tickers} missing tickers.")
        )

    unsupported_assets = sorted(set(portfolio["asset_type"]) - SUPPORTED_ASSET_TYPES)
    if unsupported_assets:
        issues.append(
            ValidationIssue(
                "ERROR",
                "unsupported_asset_types",
                f"Unsupported asset types: {unsupported_assets}. Supported: {sorted(SUPPORTED_ASSET_TYPES)}",
            )
        )

    bad_quantity_rows = portfolio["quantity"].isna() | (portfolio["quantity"] == 0)
    if bad_quantity_rows.any():
        issues.append(
            ValidationIssue(
                "ERROR",
                "bad_quantities",
                f"Found {int(bad_quantity_rows.sum())} rows with missing or zero quantity.",
            )
        )

    bad_price_rows = portfolio["price"].isna() | (portfolio["price"] <= 0)
    if bad_price_rows.any():
        issues.append(
            ValidationIssue(
                "ERROR",
                "bad_prices",
                f"Found {int(bad_price_rows.sum())} rows with missing or non-positive price.",
            )
        )

    mapped_tickers = set(factors["ticker"].dropna())
    portfolio_tickers = set(portfolio["ticker"].dropna())
    unmapped_tickers = sorted(portfolio_tickers - mapped_tickers)
    if unmapped_tickers:
        issues.append(
            ValidationIssue(
                "ERROR",
                "unmapped_tickers",
                f"Portfolio tickers missing from factor mapping: {unmapped_tickers}",
            )
        )

    option_rows = portfolio["asset_type"] == "Option"
    if option_rows.any():
        option_frame = portfolio.loc[option_rows, OPTION_REQUIRED_COLUMNS]
        missing_option_fields = option_frame.isna() | (option_frame.astype(str).apply(lambda col: col.str.strip()) == "")
        bad_option_count = int(missing_option_fields.any(axis=1).sum())

        bad_strike_count = int(
            (pd.to_numeric(portfolio.loc[option_rows, "strike"], errors="coerce") <= 0).sum()
        )

        if bad_option_count or bad_strike_count:
            issues.append(
                ValidationIssue(
                    "ERROR",
                    "bad_option_fields",
                    (
                        f"Found {bad_option_count} option rows with missing fields and "
                        f"{bad_strike_count} option rows with invalid strike."
                    ),
                )
            )

    return ValidationReport(rows_loaded=len(portfolio), issues=issues)


def print_report(report: ValidationReport) -> None:
    """Print a clean validation report for CLI users."""
    print("Portfolio Validation Report")
    print("---------------------------")
    print(f"Rows loaded: {report.rows_loaded}")

    if not report.issues:
        print("Issues: 0")
    else:
        print(f"Issues: {len(report.issues)}")
        for issue in report.issues:
            print(f"- [{issue.severity}] {issue.check_name}: {issue.message}")

    print()
    print(f"Status: {'PASS' if report.passed else 'FAIL'}")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Validate a portfolio and factor mapping file.")
    parser.add_argument("--portfolio", type=Path, required=True, help="Path to portfolio CSV.")
    parser.add_argument("--factors", type=Path, required=True, help="Path to factor mapping CSV.")
    return parser.parse_args()


def main() -> int:
    """CLI entry point."""
    args = parse_args()
    report = validate_portfolio(args.portfolio, args.factors)
    print_report(report)
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
