#include "es_engine.hpp"
#include "var_engine.hpp"

#include <stdexcept>

namespace frtb_lite {

double ExpectedShortfallEngine::historical_es(
    const std::vector<double>& losses,
    double confidence) {
  if (losses.empty()) {
    throw std::invalid_argument("historical_es requires at least one loss observation.");
  }

  const double var_threshold = VarEngine::historical_var(losses, confidence);

  double tail_sum = 0.0;
  int tail_count = 0;

  for (const double loss : losses) {
    if (loss >= var_threshold) {
      tail_sum += loss;
      ++tail_count;
    }
  }

  if (tail_count == 0) {
    return var_threshold;
  }

  return tail_sum / static_cast<double>(tail_count);
}

}  // namespace frtb_lite
