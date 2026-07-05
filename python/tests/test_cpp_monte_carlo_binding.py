"""Tests for the pybind11 C++ Monte Carlo binding."""

from __future__ import annotations

import pytest

from python.analytics.cpp_monte_carlo import calculate_cpp_var_es


def test_cpp_monte_carlo_binding_runs() -> None:
    """
    The C++ pybind11 module should run from Python after the C++ build exists.

    This test skips automatically if the extension has not been built yet.
    """
    try:
        result = calculate_cpp_var_es(
            exposures=[100000.0, 50000.0],
            covariance=[
                [0.0004, 0.00012],
                [0.00012, 0.000225],
            ],
            confidence=0.99,
            simulations=5000,
            seed=123,
        )
    except ImportError as exc:
        pytest.skip(str(exc))

    assert result["simulations"] == 5000
    assert result["var_loss"] > 0
    assert result["expected_shortfall"] >= result["var_loss"]
    assert result["tail_observations"] > 0