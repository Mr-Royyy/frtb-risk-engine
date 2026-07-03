#pragma once

#include <string>
#include <unordered_map>

namespace frtb_lite {

/**
 * @brief Mapping from an instrument ticker to risk factors.
 *
 * A major difference between a normal student project and a market-risk system
 * is that a market-risk system explains what factors drive risk. This structure
 * keeps that concept explicit. For example, AAPL may map to:
 * - AAPL_RETURN as its direct equity factor
 * - TECH_SECTOR_RETURN as a sector factor
 * - USDCAD_RETURN as a currency factor for CAD reporting
 * - AAPL_IV as an option-volatility factor
 */
struct RiskFactorMapping {
  std::string ticker;
  std::string primary_factor;
  std::string secondary_factor;
  std::string currency_factor;
  std::string volatility_factor;
  std::string bucket;
};

/**
 * @brief Convenience alias for scenario shocks.
 *
 * Keys are factor names and values are decimal shocks.
 * Example: {"US_MARKET_RETURN": -0.10} means a -10% market shock.
 */
using FactorShockMap = std::unordered_map<std::string, double>;

}  // namespace frtb_lite
