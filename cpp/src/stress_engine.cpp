#include "stress_engine.hpp"

#include <cmath>

namespace frtb_lite {
namespace {

/**
 * @brief Return a shock value if present, otherwise zero.
 */
double get_shock_or_zero(const FactorShockMap& shocks, const std::string& factor) {
  if (factor.empty()) {
    return 0.0;
  }
  const auto it = shocks.find(factor);
  if (it == shocks.end()) {
    return 0.0;
  }
  return it->second;
}

}  // namespace

std::vector<StressResult> StressEngine::run_scenario(
    const Portfolio& portfolio,
    const std::unordered_map<std::string, RiskFactorMapping>& mappings,
    const FactorShockMap& shocks) {
  std::vector<StressResult> results;
  results.reserve(portfolio.size());

  for (const auto& position : portfolio.positions()) {
    StressResult result;
    result.position_id = position.position_id;
    result.ticker = position.ticker;
    result.market_value = position.market_value();

    const auto mapping_it = mappings.find(position.ticker);
    if (mapping_it == mappings.end()) {
      results.push_back(result);
      continue;
    }

    const auto& mapping = mapping_it->second;

    const double primary = get_shock_or_zero(shocks, mapping.primary_factor);
    const double secondary = 0.5 * get_shock_or_zero(shocks, mapping.secondary_factor);
    const double currency = get_shock_or_zero(shocks, mapping.currency_factor);
    const double vol = get_shock_or_zero(shocks, mapping.volatility_factor);

    result.combined_shock = primary + secondary + currency;

    // For a long position, a negative combined shock creates a positive loss.
    result.stressed_loss = -result.market_value * result.combined_shock;

    // Simple option-volatility proxy: options can gain or lose from IV shocks.
    // The sign is simplified for MVP purposes. Future work should use Black-Scholes
    // repricing and true vega.
    if (position.asset_type == "Option") {
      const double vega_proxy = std::abs(result.market_value) * 0.10;
      result.stressed_loss += vega_proxy * std::abs(vol);
    }

    results.push_back(result);
  }

  return results;
}

}  // namespace frtb_lite
