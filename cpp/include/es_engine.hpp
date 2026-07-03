#pragma once

#include <vector>

namespace frtb_lite {

/**
 * @brief Expected Shortfall calculator.
 *
 * Expected Shortfall is the average of losses beyond the VaR threshold. It is
 * often more informative than VaR because it measures the severity of the tail,
 * not just the percentile cutoff.
 */
class ExpectedShortfallEngine {
 public:
  /**
   * @brief Compute historical Expected Shortfall from losses.
   *
   * @param losses Positive-loss vector.
   * @param confidence Confidence level used for the tail threshold.
   * @return Average tail loss at or beyond VaR.
   */
  [[nodiscard]] static double historical_es(
      const std::vector<double>& losses,
      double confidence);
};

}  // namespace frtb_lite
