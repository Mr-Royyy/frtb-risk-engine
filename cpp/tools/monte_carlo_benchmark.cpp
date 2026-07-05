#include "monte_carlo_engine.hpp"

#include <chrono>
#include <cstddef>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <vector>

/**
 * @brief Benchmark executable for the C++ Monte Carlo risk engine.
 *
 * This tool is intentionally simple:
 * - It creates a small synthetic multi-factor portfolio.
 * - It runs Monte Carlo VaR / Expected Shortfall.
 * - It reports elapsed runtime and risk metrics.
 *
 * The purpose is to make the C++ risk core visible from the command line and
 * provide a clean benchmark artifact for the project README.
 */
int main() {
  using frtb_lite::MonteCarloEngine;

  const std::vector<double> exposures = {
      100000.0,
      75000.0,
      50000.0,
      25000.0,
      15000.0,
  };

  const std::vector<std::vector<double>> covariance = {
      {0.000400, 0.000120, 0.000080, 0.000040, 0.000020},
      {0.000120, 0.000300, 0.000070, 0.000030, 0.000015},
      {0.000080, 0.000070, 0.000225, 0.000025, 0.000010},
      {0.000040, 0.000030, 0.000025, 0.000144, 0.000008},
      {0.000020, 0.000015, 0.000010, 0.000008, 0.000100},
  };

  const double confidence = 0.99;
  const std::size_t simulations = 250000;
  const std::uint32_t seed = 123;

  const auto start = std::chrono::high_resolution_clock::now();

  const auto result = MonteCarloEngine::calculate_var_es(
      exposures,
      covariance,
      confidence,
      simulations,
      seed);

  const auto end = std::chrono::high_resolution_clock::now();

  const auto elapsed_ms =
      std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();

  std::cout << "C++ Monte Carlo Benchmark\n";
  std::cout << "-------------------------\n";
  std::cout << std::fixed << std::setprecision(2);
  std::cout << "Simulations: " << result.simulations << "\n";
  std::cout << "Confidence: " << confidence * 100.0 << "%\n";
  std::cout << "VaR loss: $" << result.var_loss << "\n";
  std::cout << "Expected Shortfall: $" << result.expected_shortfall << "\n";
  std::cout << "Mean loss: $" << result.mean_loss << "\n";
  std::cout << "Tail observations: " << result.tail_observations << "\n";
  std::cout << "Elapsed time: " << elapsed_ms << " ms\n";

  return 0;
}