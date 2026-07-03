#pragma once

#include <vector>

namespace frtb_lite {

/**
 * @brief Historical Value-at-Risk calculator.
 *
 * Convention:
 * - Input values are losses, not returns.
 * - Positive numbers represent losses.
 * - A 99% VaR is the loss threshold exceeded by roughly 1% of outcomes.
 *
 * Example:
 * losses = {10, 20, 30, 100}
 * confidence = 0.99
 * VaR will select a high percentile loss from the empirical distribution.
 */
class VarEngine {
 public:
  /**
   * @brief Compute historical VaR from a vector of portfolio losses.
   *
   * @param losses Positive-loss vector.
   * @param confidence Confidence level, such as 0.95 or 0.99.
   * @return VaR loss threshold.
   */
  [[nodiscard]] static double historical_var(
      const std::vector<double>& losses,
      double confidence);
};

}  // namespace frtb_lite
