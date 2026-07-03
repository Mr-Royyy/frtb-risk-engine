#pragma once

#include <string>

namespace frtb_lite {

/**
 * @brief Represents one position in the market-risk portfolio.
 *
 * The first milestone of the project keeps the instrument model intentionally
 * simple. Each position has a quantity, a price, an asset type, and optional
 * option metadata. More advanced versions can replace this with a polymorphic
 * instrument hierarchy such as EquityPosition, FxPosition, OptionPosition, etc.
 *
 * Design convention:
 * - quantity is positive for a long position and negative for a short position.
 * - price is the current mark/market price in the position currency.
 * - market_value = quantity * price.
 */
struct Position {
  std::string position_id;
  std::string asset_type;
  std::string ticker;
  double quantity = 0.0;
  double price = 0.0;
  std::string currency;
  std::string sector;
  std::string asset_class;

  // Option fields are optional for non-option instruments.
  std::string option_type;
  double strike = 0.0;
  std::string maturity;

  /**
   * @brief Current marked market value of the position.
   *
   * For this starter version, this is a simple quantity * price calculation.
   * Future versions can add contract multipliers, FX conversion, accrued
   * interest, clean/dirty bond prices, and option contract sizes.
   */
  [[nodiscard]] double market_value() const;
};

}  // namespace frtb_lite
