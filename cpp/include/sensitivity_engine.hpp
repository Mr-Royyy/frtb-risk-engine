#pragma once

#include "portfolio.hpp"
#include "risk_factor.hpp"

#include <string>
#include <unordered_map>
#include <vector>

namespace frtb_lite {

/**
 * @brief Simplified FRTB-lite sensitivity output.
 *
 * This is deliberately not a full FRTB standardized-approach implementation.
 * It is a compact educational representation of delta, vega, and curvature-like
 * risk concepts that can later be expanded into true regulatory buckets.
 */
struct SensitivityResult {
  std::string ticker;
  std::string bucket;
  double delta_exposure = 0.0;
  double vega_proxy = 0.0;
  double curvature_proxy = 0.0;
};

/**
 * @brief Simplified sensitivities engine.
 *
 * The starter logic is intentionally transparent:
 * - delta exposure is approximated by market value.
 * - vega proxy is used only for option-like positions.
 * - curvature proxy is a small nonlinear add-on for option-like positions.
 *
 * This is useful for a dashboard MVP, but the methodology page should clearly
 * explain that true option Greeks and Basel aggregation rules are future work.
 */
class SensitivityEngine {
 public:
  /**
   * @brief Compute simplified sensitivity-style exposures.
   */
  [[nodiscard]] static std::vector<SensitivityResult> compute(
      const Portfolio& portfolio,
      const std::unordered_map<std::string, RiskFactorMapping>& mappings);
};

}  // namespace frtb_lite
