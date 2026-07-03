#include "backtest_engine.hpp"

#include <stdexcept>

namespace frtb_lite {

BacktestSummary BacktestEngine::summarize(
    const std::vector<double>& realized_losses,
    const std::vector<double>& forecast_var) {
  if (realized_losses.size() != forecast_var.size()) {
    throw std::invalid_argument("realized_losses and forecast_var must have the same length.");
  }

  BacktestSummary summary;
  summary.observations = static_cast<int>(realized_losses.size());

  double exception_loss_sum = 0.0;

  for (std::size_t i = 0; i < realized_losses.size(); ++i) {
    if (realized_losses[i] > forecast_var[i]) {
      ++summary.exceptions;
      exception_loss_sum += realized_losses[i];
    }
  }

  if (summary.observations > 0) {
    summary.exception_rate =
        static_cast<double>(summary.exceptions) / static_cast<double>(summary.observations);
  }

  if (summary.exceptions > 0) {
    summary.average_exception_loss =
        exception_loss_sum / static_cast<double>(summary.exceptions);
  }

  return summary;
}

}  // namespace frtb_lite
