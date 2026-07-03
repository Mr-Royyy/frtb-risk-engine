#pragma once

#include <vector>

namespace frtb_lite {

/**
 * @brief Summary output for a VaR backtest.
 */
struct BacktestSummary {
  int observations = 0;
  int exceptions = 0;
  double exception_rate = 0.0;
  double average_exception_loss = 0.0;
};

/**
 * @brief Basic VaR backtesting helper.
 *
 * The engine compares realized losses against forecast VaR numbers. If realized
 * loss > VaR, the day is counted as an exception/breach.
 */
class BacktestEngine {
 public:
  /**
   * @brief Count exceptions and summarize exception severity.
   *
   * @param realized_losses Positive-loss vector.
   * @param forecast_var Matching vector of forecast VaR values.
   * @return BacktestSummary with exception count and severity.
   */
  [[nodiscard]] static BacktestSummary summarize(
      const std::vector<double>& realized_losses,
      const std::vector<double>& forecast_var);
};

}  // namespace frtb_lite
