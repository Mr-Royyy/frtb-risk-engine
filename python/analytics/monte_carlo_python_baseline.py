"""
Python baseline benchmark for Monte Carlo VaR / Expected Shortfall.

This script mirrors the C++ benchmark with the same exposures, covariance
matrix, confidence level, simulation count, and random seed.

The goal is not to make Python look bad. The goal is to show that the project
has a real benchmark workflow and that the C++ engine can be evaluated against
a transparent Python/Numpy baseline.
"""

from __future__ import annotations

import time

import numpy as np


def historical_var(losses: np.ndarray, confidence: float) -> float:
    """Calculate empirical VaR from a simulated loss distribution."""
    return float(np.quantile(losses, confidence, method="higher"))


def expected_shortfall(losses: np.ndarray, confidence: float) -> float:
    """Calculate Expected Shortfall from simulated losses."""
    var_loss = historical_var(losses, confidence)
    tail_losses = losses[losses >= var_loss]

    if tail_losses.size == 0:
        return var_loss

    return float(tail_losses.mean())


def main() -> int:
    """Run the Python Monte Carlo benchmark."""
    exposures = np.array(
        [
            100000.0,
            75000.0,
            50000.0,
            25000.0,
            15000.0,
        ]
    )

    covariance = np.array(
        [
            [0.000400, 0.000120, 0.000080, 0.000040, 0.000020],
            [0.000120, 0.000300, 0.000070, 0.000030, 0.000015],
            [0.000080, 0.000070, 0.000225, 0.000025, 0.000010],
            [0.000040, 0.000030, 0.000025, 0.000144, 0.000008],
            [0.000020, 0.000015, 0.000010, 0.000008, 0.000100],
        ]
    )

    confidence = 0.99
    simulations = 250_000
    seed = 123

    rng = np.random.default_rng(seed)

    start = time.perf_counter()

    simulated_returns = rng.multivariate_normal(
        mean=np.zeros(len(exposures)),
        cov=covariance,
        size=simulations,
    )

    pnl = simulated_returns @ exposures
    losses = -pnl

    var_loss = historical_var(losses, confidence)
    es_loss = expected_shortfall(losses, confidence)
    mean_loss = float(losses.mean())
    tail_observations = int((losses >= var_loss).sum())

    elapsed_ms = (time.perf_counter() - start) * 1000.0

    print("Python Monte Carlo Benchmark")
    print("----------------------------")
    print(f"Simulations: {simulations}")
    print(f"Confidence: {confidence:.2%}")
    print(f"VaR loss: ${var_loss:,.2f}")
    print(f"Expected Shortfall: ${es_loss:,.2f}")
    print(f"Mean loss: ${mean_loss:,.2f}")
    print(f"Tail observations: {tail_observations}")
    print(f"Elapsed time: {elapsed_ms:,.0f} ms")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())