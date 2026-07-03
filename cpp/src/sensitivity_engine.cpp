#include "sensitivity_engine.hpp"

#include <cmath>

namespace frtb_lite {

std::vector<SensitivityResult> SensitivityEngine::compute(
    const Portfolio& portfolio,
    const std::unordered_map<std::string, RiskFactorMapping>& mappings) {
  std::vector<SensitivityResult> results;
  results.reserve(portfolio.size());

  for (const auto& position : portfolio.positions()) {
    SensitivityResult result;
    result.ticker = position.ticker;
    result.delta_exposure = position.market_value();

    const auto mapping_it = mappings.find(position.ticker);
    if (mapping_it != mappings.end()) {
      result.bucket = mapping_it->second.bucket;
    }

    if (position.asset_type == "Option") {
      // Starter proxies only. Replace with Black-Scholes Greeks in Milestone 5.
      result.vega_proxy = std::abs(position.market_value()) * 0.10;
      result.curvature_proxy = std::abs(position.market_value()) * 0.02;
    }

    results.push_back(result);
  }

  return results;
}

}  // namespace frtb_lite
