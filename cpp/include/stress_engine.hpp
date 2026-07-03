#pragma once

#include "portfolio.hpp"
#include "risk_factor.hpp"

#include <string>
#include <unordered_map>
#include <vector>

namespace frtb_lite {

/**
 * @brief Position-level stress test result.
 */
struct StressResult {
  std::string position_id;
  std::string ticker;
  double market_value = 0.0;
  double combined_shock = 0.0;
  double stressed_loss = 0.0;
};

/**
 * @brief Simplified factor-shock stress engine.
 *
 * This starter engine applies mapped factor shocks to each position. It is not a
 * full pricing engine. The purpose is to provide a clear and extendable stress
 * testing module:
 *
 * - Primary factor receives full weight.
 * - Secondary factor receives partial weight.
 * - Currency factor receives full weight.
 * - Volatility factor adds a simple option proxy loss.
 *
 * Future versions should replace this linear approximation with true repricing
 * for options, rates, credit, and multi-currency portfolios.
 */
class StressEngine {
 public:
  /**
   * @brief Apply a factor-shock scenario to a portfolio.
   *
   * @param portfolio Portfolio to shock.
   * @param mappings Risk-factor mapping keyed by ticker.
   * @param shocks Scenario shock values keyed by factor name.
   * @return Position-level stress losses.
   */
  [[nodiscard]] static std::vector<StressResult> run_scenario(
      const Portfolio& portfolio,
      const std::unordered_map<std::string, RiskFactorMapping>& mappings,
      const FactorShockMap& shocks);
};

}  // namespace frtb_lite
