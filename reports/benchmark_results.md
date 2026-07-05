# Benchmark Results

## Purpose

This benchmark compares the C++ Monte Carlo risk engine against a Python/Numpy
baseline using the same synthetic portfolio, covariance matrix, confidence
level, simulation count, and random seed.

The goal is not to claim universal C++ superiority. The goal is to show that the
project has a real risk-engine benchmark workflow and that the C++ core can be
tested independently from the dashboard.

## Environment

- Operating system: Windows-10-10.0.26200-SP0
- Python version: 3.11.9
- Machine-specific note: benchmark timing depends on CPU, compiler, build mode, and background processes.

## Summary

| Engine | Elapsed Time | VaR Loss | Expected Shortfall | Mean Loss | Tail Observations |
| --- | ---: | ---: | ---: | ---: | ---: |
| C++ Monte Carlo | 152.0 ms | $7333.31 | $8386.95 | $-9.91 | 2501 |
| Python/Numpy Baseline | 76.0 ms | $7,382.67 | $8,418.87 | $8.11 | 2500 |

Relative runtime:

```text
0.50x
```

## C++ benchmark output

```text
C++ Monte Carlo Benchmark
-------------------------
Simulations: 250000
Confidence: 99.00%
VaR loss: $7333.31
Expected Shortfall: $8386.95
Mean loss: $-9.91
Tail observations: 2501
Elapsed time: 152 ms
```

## Python benchmark output

```text
Python Monte Carlo Benchmark
----------------------------
Simulations: 250000
Confidence: 99.00%
VaR loss: $7,382.67
Expected Shortfall: $8,418.87
Mean loss: $8.11
Tail observations: 2500
Elapsed time: 76 ms
```

## Interpretation

The C++ benchmark demonstrates that the project contains an independently
compiled quantitative risk engine. The Python/Numpy benchmark provides a
transparent vectorized baseline for comparison and validation.

In this run, the Python/Numpy baseline was faster than the current scalar C++
implementation. This is expected to be possible because NumPy uses optimized
compiled numerical routines under the hood. The benchmark still proves that the
C++ engine builds, runs, and produces comparable VaR / Expected Shortfall
outputs.

Future optimization work could reduce C++ runtime by avoiding per-path memory
allocation, adding Eigen-based matrix operations, using OpenMP parallelism, or
exposing the engine to Python through pybind11.
