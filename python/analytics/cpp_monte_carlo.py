"""
Python wrapper for the optimized C++ Monte Carlo risk engine.

This file demonstrates the intended C++/Python architecture:

- C++ handles the high-performance quantitative risk calculation.
- Python handles orchestration, reporting, validation, testing, and dashboard integration.

The wrapper loads the compiled pybind11 module from the local CMake build
directory and exposes a small Python-friendly function.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CPP_RELEASE_DIR = PROJECT_ROOT / "cpp" / "build" / "Release"
CPP_DEBUG_DIR = PROJECT_ROOT / "cpp" / "build" / "Debug"
CPP_BUILD_DIR = PROJECT_ROOT / "cpp" / "build"

for path in [CPP_RELEASE_DIR, CPP_DEBUG_DIR, CPP_BUILD_DIR]:
    if path.exists() and str(path) not in sys.path:
        sys.path.append(str(path))


def load_cpp_module() -> Any:
    """
    Load the compiled pybind11 module.

    Raises a clear error if the C++ extension has not been built yet.
    """
    try:
        import frtb_lite_cpp  # type: ignore

        return frtb_lite_cpp
    except ImportError as exc:
        raise ImportError(
            "Could not import frtb_lite_cpp. Build the C++ pybind11 module first:\n\n"
            "cmake -S cpp -B cpp\\build -G \"Visual Studio 17 2022\" -A x64\n"
            "cmake --build cpp\\build --config Release\n"
        ) from exc


def run_cpp_monte_carlo_example() -> dict[str, float | int]:
    """
    Run a small C++ Monte Carlo VaR / ES example from Python.
    """
    cpp = load_cpp_module()

    result = cpp.calculate_var_es(
        [100000.0, 50000.0],
        [
            [0.0004, 0.00012],
            [0.00012, 0.000225],
        ],
        0.99,
        5000,
        123,
    )

    return {
        "var_loss": float(result.var_loss),
        "expected_shortfall": float(result.expected_shortfall),
        "mean_loss": float(result.mean_loss),
        "simulations": int(result.simulations),
        "tail_observations": int(result.tail_observations),
    }


def calculate_cpp_var_es(
    exposures: list[float],
    covariance: list[list[float]],
    confidence: float = 0.99,
    simulations: int = 250_000,
    seed: int = 123,
) -> dict[str, float | int]:
    """
    Python-friendly wrapper around the C++ Monte Carlo VaR / ES engine.
    """
    cpp = load_cpp_module()

    result = cpp.calculate_var_es(
        exposures,
        covariance,
        confidence,
        simulations,
        seed,
    )

    return {
        "var_loss": float(result.var_loss),
        "expected_shortfall": float(result.expected_shortfall),
        "mean_loss": float(result.mean_loss),
        "simulations": int(result.simulations),
        "tail_observations": int(result.tail_observations),
    }


def main() -> int:
    """CLI entry point."""
    result = run_cpp_monte_carlo_example()

    print("C++ Monte Carlo called from Python")
    print("----------------------------------")
    print(f"VaR loss: ${result['var_loss']:,.2f}")
    print(f"Expected Shortfall: ${result['expected_shortfall']:,.2f}")
    print(f"Mean loss: ${result['mean_loss']:,.2f}")
    print(f"Simulations: {result['simulations']}")
    print(f"Tail observations: {result['tail_observations']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())