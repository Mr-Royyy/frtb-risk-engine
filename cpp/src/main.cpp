#include "backtest_engine.hpp"
#include "es_engine.hpp"
#include "portfolio.hpp"
#include "stress_engine.hpp"
#include "var_engine.hpp"

#include <iostream>
#include <unordered_map>
#include <vector>

using namespace frtb_lite;

/**
 * @brief Small command-line demo for checking the C++ risk core.
 *
 * This is intentionally simple. The Python layer is responsible for real CSV
 * loading in the starter repo. Later, the C++ layer can receive a robust CSV
 * parser and full command-line interface.
 */
int main() {
  Portfolio portfolio;
  portfolio.add_position({"P001", "Equity", "AAPL", 100.0, 210.50, "USD", "Technology", "Equity"});
  portfolio.add_position({"P002", "Equity", "MSFT", 75.0, 430.20, "USD", "Technology", "Equity"});

  std::vector<double> losses = {100, 250, 90, 400, 50, 700, 120, 80, 300, 1000};

  const double var_95 = VarEngine::historical_var(losses, 0.95);
  const double es_95 = ExpectedShortfallEngine::historical_es(losses, 0.95);

  std::cout << "FRTB-Lite C++ demo\\n";
  std::cout << "Positions: " << portfolio.size() << "\\n";
  std::cout << "Market value: " << portfolio.total_market_value() << "\\n";
  std::cout << "Historical VaR 95%: " << var_95 << "\\n";
  std::cout << "Historical ES 95%: " << es_95 << "\\n";

  std::unordered_map<std::string, RiskFactorMapping> mappings;
  mappings["AAPL"] = {"AAPL", "AAPL_RETURN", "TECH_SECTOR_RETURN", "USDCAD_RETURN", "AAPL_IV", "US_EQ_TECH"};
  mappings["MSFT"] = {"MSFT", "MSFT_RETURN", "TECH_SECTOR_RETURN", "USDCAD_RETURN", "MSFT_IV", "US_EQ_TECH"};

  FactorShockMap shocks = {
      {"AAPL_RETURN", -0.10},
      {"MSFT_RETURN", -0.08},
      {"TECH_SECTOR_RETURN", -0.12},
      {"USDCAD_RETURN", 0.02},
  };

  const auto stress_results = StressEngine::run_scenario(portfolio, mappings, shocks);

  double total_stress_loss = 0.0;
  for (const auto& result : stress_results) {
    total_stress_loss += result.stressed_loss;
  }

  std::cout << "Sample stress loss: " << total_stress_loss << "\\n";

  return 0;
}
