#pragma once

#include "position.hpp"

#include <string>
#include <vector>

namespace frtb_lite {

/**
 * @brief Container for portfolio positions and aggregation utilities.
 *
 * In a production market-risk engine, a Portfolio would also include valuation
 * date, book, desk, base currency, legal entity, and model-eligibility metadata.
 * This project starts with the minimum necessary structure so the risk math can
 * be built cleanly.
 */
class Portfolio {
 public:
  /**
   * @brief Add a position to the portfolio.
   */
  void add_position(const Position& position);

  /**
   * @brief Read-only access to all positions.
   */
  [[nodiscard]] const std::vector<Position>& positions() const;

  /**
   * @brief Total marked value across all positions.
   *
   * This starter assumes every position is already expressed in a comparable
   * reporting currency. The Python layer is the right place to add explicit FX
   * conversion in the next milestone.
   */
  [[nodiscard]] double total_market_value() const;

  /**
   * @brief Number of positions in the portfolio.
   */
  [[nodiscard]] std::size_t size() const;

 private:
  std::vector<Position> positions_;
};

}  // namespace frtb_lite
