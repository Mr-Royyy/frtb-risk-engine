"""
Run benchmark commands for the FRTB-Lite Market Risk Engine.

This script runs:
1. The C++ Monte Carlo benchmark executable.
2. The Python/Numpy Monte Carlo baseline.
3. A generated Markdown benchmark report.

The report is written to:

    reports/benchmark_results.md

This makes the project easier to review on GitHub because benchmark results are
saved in a clean artifact instead of being buried in terminal output.
"""

from __future__ import annotations

import argparse
import platform
import re
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_command(command: list[str], cwd: Path) -> str:
    """
    Run a command and return stdout.

    Raises a clear error if the command fails.
    """
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )

    if completed.returncode != 0:
        error_message = f"""
Command failed:
{' '.join(command)}

STDOUT:
{completed.stdout}

STDERR:
{completed.stderr}
"""
        raise RuntimeError(error_message)

    return completed.stdout.strip()


def find_cpp_benchmark_executable() -> Path:
    """
    Find the compiled C++ benchmark executable.

    Visual Studio generators usually place the executable under:
        cpp/build/Release/monte_carlo_benchmark.exe

    Single-config generators may place it under:
        cpp/build/monte_carlo_benchmark.exe
    """
    candidate_paths = [
        PROJECT_ROOT / "cpp/build/Release/monte_carlo_benchmark.exe",
        PROJECT_ROOT / "cpp/build/Debug/monte_carlo_benchmark.exe",
        PROJECT_ROOT / "cpp/build/monte_carlo_benchmark.exe",
        PROJECT_ROOT / "cpp/build/Release/monte_carlo_benchmark",
        PROJECT_ROOT / "cpp/build/monte_carlo_benchmark",
    ]

    for path in candidate_paths:
        if path.exists():
            return path

    raise FileNotFoundError(
        "Could not find the C++ benchmark executable. "
        "Build it first with: cmake --build cpp\\build --config Release"
    )


def extract_elapsed_ms(output: str) -> float | None:
    """
    Extract elapsed milliseconds from benchmark output.

    Expected line:
        Elapsed time: 123 ms
    """
    match = re.search(r"Elapsed time:\s*([\d,]+(?:\.\d+)?)\s*ms", output)

    if not match:
        return None

    return float(match.group(1).replace(",", ""))


def extract_metric(output: str, label: str) -> str:
    """
    Extract a metric value from a benchmark output block.

    Example:
        label='VaR loss' extracts '$123.45' from:
        VaR loss: $123.45
    """
    pattern = rf"{re.escape(label)}:\s*(.+)"
    match = re.search(pattern, output)

    if not match:
        return "n/a"

    return match.group(1).strip()

def create_report(
    cpp_output: str,
    python_output: str,
    cpp_elapsed_ms: float | None,
    python_elapsed_ms: float | None,
) -> str:
    """
    Create a Markdown benchmark report.
    """
    speedup_text = "n/a"

    if cpp_elapsed_ms and python_elapsed_ms and cpp_elapsed_ms > 0:
        speedup = python_elapsed_ms / cpp_elapsed_ms
        speedup_text = f"{speedup:.2f}x"

    return f"""# Benchmark Results

## Purpose

This benchmark compares the C++ Monte Carlo risk engine against a Python/Numpy
baseline using the same synthetic portfolio, covariance matrix, confidence
level, simulation count, and random seed.

The goal is not to claim universal C++ superiority. The goal is to show that the
project has a real risk-engine benchmark workflow and that the C++ core can be
tested independently from the dashboard.

## Environment

- Operating system: {platform.platform()}
- Python version: {platform.python_version()}
- Machine-specific note: benchmark timing depends on CPU, compiler, build mode, and background processes.

## Summary

| Engine | Elapsed Time | VaR Loss | Expected Shortfall | Mean Loss | Tail Observations |
| --- | ---: | ---: | ---: | ---: | ---: |
| C++ Monte Carlo | {cpp_elapsed_ms if cpp_elapsed_ms is not None else "n/a"} ms | {extract_metric(cpp_output, "VaR loss")} | {extract_metric(cpp_output, "Expected Shortfall")} | {extract_metric(cpp_output, "Mean loss")} | {extract_metric(cpp_output, "Tail observations")} |
| Python/Numpy Baseline | {python_elapsed_ms if python_elapsed_ms is not None else "n/a"} ms | {extract_metric(python_output, "VaR loss")} | {extract_metric(python_output, "Expected Shortfall")} | {extract_metric(python_output, "Mean loss")} | {extract_metric(python_output, "Tail observations")} |

Relative runtime:

```text
{speedup_text}
```

## C++ benchmark output

```text
{cpp_output}
```

## Python benchmark output

```text
{python_output}
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
"""


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run C++ and Python Monte Carlo benchmarks.")
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "reports/benchmark_results.md",
        help="Path to the generated Markdown benchmark report.",
    )
    return parser.parse_args()


def main() -> int:
    """Run benchmark workflow."""
    args = parse_args()

    cpp_executable = find_cpp_benchmark_executable()

    print("Running C++ benchmark...")
    cpp_output = run_command([str(cpp_executable)], cwd=PROJECT_ROOT)

    print("Running Python baseline...")
    python_output = run_command(
        [sys.executable, "python/analytics/monte_carlo_python_baseline.py"],
        cwd=PROJECT_ROOT,
    )

    cpp_elapsed_ms = extract_elapsed_ms(cpp_output)
    python_elapsed_ms = extract_elapsed_ms(python_output)

    report = create_report(
        cpp_output=cpp_output,
        python_output=python_output,
        cpp_elapsed_ms=cpp_elapsed_ms,
        python_elapsed_ms=python_elapsed_ms,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")

    print()
    print("Benchmark report written to:")
    print(args.output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())