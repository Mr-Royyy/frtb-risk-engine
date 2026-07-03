#include "var_engine.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace frtb_lite {

double VarEngine::historical_var(
    const std::vector<double>& losses,
    double confidence) {
  if (losses.empty()) {
    throw std::invalid_argument("historical_var requires at least one loss observation.");
  }
  if (confidence <= 0.0 || confidence >= 1.0) {
    throw std::invalid_argument("confidence must be between 0 and 1.");
  }

  std::vector<double> sorted_losses = losses;
  std::sort(sorted_losses.begin(), sorted_losses.end());

  // Nearest-rank style empirical quantile.
  const auto n = static_cast<double>(sorted_losses.size());
  std::size_t index = static_cast<std::size_t>(std::ceil(confidence * n)) - 1;
  index = std::min(index, sorted_losses.size() - 1);

  return sorted_losses[index];
}

}  // namespace frtb_lite
