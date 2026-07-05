#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

namespace frtb_lite {

/**
 * @brief Output from a Monte Carlo VaR / Expected Shortfall run.
 *
 * Convention:
 * - Positive values represent losses.
 * - VaR is the selected tail percentile of simulated losses.
 * - Expected Shortfall is the average of losses at or beyond VaR.
 */
struct MonteCarloResult {
  double var_loss{0.0};
  double expected_shortfall{0.0};
  double mean_loss{0.0};
  std::size_t simulations{0};
  std::size_t tail_observations{0};
};

/**
 * @brief Monte Carlo engine for market-risk loss simulation.
 *
 * The engine simulates correlated normal factor returns using a covariance
 * matrix and a Cholesky decomposition. Portfolio P&L is then approximated as:
 *
 *   P&L = sum(exposure_i * factor_return_i)
 *
 * Loss is defined as:
 *
 *   loss = -P&L
 *
 * This is intentionally simple and transparent. It is useful for demonstrating
 * the C++ risk-core architecture before adding more advanced pricing models.
 */
class MonteCarloEngine {
 public:
  /**
   * @brief Simulate a portfolio loss distribution.
   *
   * @param exposures Dollar exposure to each risk factor.
   * @param covariance Square covariance matrix for the risk factors.
   * @param simulations Number of Monte Carlo paths.
   * @param seed Random seed for deterministic tests and reproducible runs.
   * @return Vector of simulated positive/negative losses.
   */
  [[nodiscard]] static std::vector<double> simulate_losses(
      const std::vector<double>& exposures,
      const std::vector<std::vector<double>>& covariance,
      std::size_t simulations,
      std::uint32_t seed = 42);

  /**
   * @brief Simulate losses and calculate VaR / Expected Shortfall.
   *
   * @param exposures Dollar exposure to each risk factor.
   * @param covariance Square covariance matrix for the risk factors.
   * @param confidence Confidence level, such as 0.95 or 0.99.
   * @param simulations Number of Monte Carlo paths.
   * @param seed Random seed for reproducibility.
   * @return MonteCarloResult containing VaR, ES, mean loss, and tail count.
   */
  [[nodiscard]] static MonteCarloResult calculate_var_es(
      const std::vector<double>& exposures,
      const std::vector<std::vector<double>>& covariance,
      double confidence,
      std::size_t simulations,
      std::uint32_t seed = 42);

 private:
  /**
   * @brief Compute lower-triangular Cholesky factor.
   *
   * This expects a symmetric positive semi-definite covariance matrix. A tiny
   * numerical floor is used on the diagonal to keep the educational starter
   * stable when sample covariance values are close to zero.
   */
  [[nodiscard]] static std::vector<std::vector<double>> cholesky_decompose(
      const std::vector<std::vector<double>>& matrix);

  /**
   * @brief Validate exposure vector and covariance matrix dimensions.
   */
  static void validate_inputs(
      const std::vector<double>& exposures,
      const std::vector<std::vector<double>>& covariance,
      std::size_t simulations);
};

}  // namespace frtb_lite