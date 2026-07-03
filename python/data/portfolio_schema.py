"""
Portfolio schema definitions for the FRTB-Lite Market Risk Engine.

This module keeps the portfolio data contract in one place. In market-risk
systems, the data contract matters as much as the model because bad input data
can make a risk number meaningless. The validator imports these constants so
that the required columns and allowed asset types are documented in code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


REQUIRED_PORTFOLIO_COLUMNS: Final[list[str]] = [
    "position_id",
    "asset_type",
    "ticker",
    "quantity",
    "price",
    "currency",
    "sector",
    "asset_class",
    "option_type",
    "strike",
    "maturity",
]

REQUIRED_FACTOR_COLUMNS: Final[list[str]] = [
    "ticker",
    "primary_factor",
    "secondary_factor",
    "currency_factor",
    "vol_factor",
    "bucket",
]

SUPPORTED_ASSET_TYPES: Final[set[str]] = {"Equity", "ETF", "FX", "Option"}

OPTION_REQUIRED_COLUMNS: Final[list[str]] = ["option_type", "strike", "maturity"]


@dataclass(frozen=True)
class ValidationIssue:
    """One data-quality issue found during portfolio validation."""

    severity: str
    check_name: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    """Structured result returned by the portfolio validator."""

    rows_loaded: int
    issues: list[ValidationIssue]

    @property
    def passed(self) -> bool:
        """Return True when no error-level validation issues were found."""
        return not any(issue.severity.upper() == "ERROR" for issue in self.issues)
