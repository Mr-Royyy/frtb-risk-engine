#include "portfolio.hpp"

#include <numeric>

namespace frtb_lite {

double Position::market_value() const {
  return quantity * price;
}

void Portfolio::add_position(const Position& position) {
  positions_.push_back(position);
}

const std::vector<Position>& Portfolio::positions() const {
  return positions_;
}

double Portfolio::total_market_value() const {
  double total = 0.0;
  for (const auto& position : positions_) {
    total += position.market_value();
  }
  return total;
}

std::size_t Portfolio::size() const {
  return positions_.size();
}

}  // namespace frtb_lite
