#include "backtest_engine.hpp"
#include "es_engine.hpp"
#include "portfolio.hpp"
#include "stress_engine.hpp"
#include "var_engine.hpp"

#include "monte_carlo_engine.hpp"

#include <cmath>
#include <iostream>
#include <stdexcept>
#include <unordered_map>
#include <vector>

using namespace frtb_lite;

namespace
{

  /**
   * @brief Tiny assertion helper to avoid external C++ test dependencies.
   *
   * A production repo would usually use GoogleTest or Catch2. This starter keeps
   * tests dependency-free so the first build is easy on any machine.
   */
  void require(bool condition, const char *message)
  {
    if (!condition)
    {
      throw std::runtime_error(message);
    }
  }

  void require_near(double actual, double expected, double tolerance, const char *message)
  {
    if (std::fabs(actual - expected) > tolerance)
    {
      std::cerr << "Expected " << expected << " but got " << actual << "\\n";
      throw std::runtime_error(message);
    }
  }

} // namespace

int main()
{
  {
    Portfolio portfolio;
    portfolio.add_position({"P001", "Equity", "AAPL", 100.0, 200.0, "USD", "Technology", "Equity"});
    portfolio.add_position({"P002", "Equity", "MSFT", 50.0, 400.0, "USD", "Technology", "Equity"});

    require(portfolio.size() == 2, "portfolio size should be 2");
    require_near(portfolio.total_market_value(), 40000.0, 1e-9, "portfolio market value mismatch");
  }

  {
    std::vector<double> losses = {10, 20, 30, 40, 50, 100};
    const double var_95 = VarEngine::historical_var(losses, 0.95);
    const double es_95 = ExpectedShortfallEngine::historical_es(losses, 0.95);

    require_near(var_95, 100.0, 1e-9, "VaR 95 should pick the highest loss for this sample");
    require_near(es_95, 100.0, 1e-9, "ES 95 should equal tail loss for this sample");
  }

  {
    std::vector<double> realized = {10, 20, 200, 30};
    std::vector<double> forecast = {50, 50, 100, 50};

    const auto summary = BacktestEngine::summarize(realized, forecast);

    require(summary.observations == 4, "backtest observation count mismatch");
    require(summary.exceptions == 1, "backtest exception count mismatch");
    require_near(summary.exception_rate, 0.25, 1e-9, "backtest exception rate mismatch");
  }

  {
    Portfolio portfolio;
    portfolio.add_position({"P001", "Equity", "AAPL", 100.0, 200.0, "USD", "Technology", "Equity"});

    std::unordered_map<std::string, RiskFactorMapping> mappings;
    mappings["AAPL"] = {"AAPL", "AAPL_RETURN", "TECH_SECTOR_RETURN", "", "", "US_EQ_TECH"};

    FactorShockMap shocks = {
        {"AAPL_RETURN", -0.10},
        {"TECH_SECTOR_RETURN", -0.10},
    };

    const auto results = StressEngine::run_scenario(portfolio, mappings, shocks);

    require(results.size() == 1, "stress result size mismatch");
    require(results[0].stressed_loss > 0.0, "equity selloff should create positive loss for long position");
  }

  {
    // Two-factor Monte Carlo example:
    // - factor 1 has 2% daily volatility
    // - factor 2 has 1.5% daily volatility
    // - covariance creates moderate positive relationship between factors
    std::vector<double> exposures = {100000.0, 50000.0};

    std::vector<std::vector<double>> covariance = {
        {0.0004, 0.00012},
        {0.00012, 0.000225},
    };

    const auto result = MonteCarloEngine::calculate_var_es(
        exposures,
        covariance,
        0.99,
        5000,
        123);

    require(result.simulations == 5000, "Monte Carlo simulation count mismatch");
    require(result.var_loss > 0.0, "Monte Carlo VaR should be positive for risky exposure");
    require(
        result.expected_shortfall >= result.var_loss,
        "Monte Carlo ES should be greater than or equal to VaR");
    require(result.tail_observations > 0, "Monte Carlo tail observations should be positive");
  }

  {
    bool threw = false;

    try
    {
      std::vector<double> exposures = {100000.0, 50000.0};
      std::vector<std::vector<double>> bad_covariance = {
          {0.0004},
      };

      (void)MonteCarloEngine::calculate_var_es(
          exposures,
          bad_covariance,
          0.99,
          1000,
          123);
    }
    catch (const std::invalid_argument &)
    {
      threw = true;
    }

    require(threw, "Monte Carlo engine should reject invalid covariance dimensions");
  }

  std::cout << "All C++ risk-engine tests passed.\\n";
  return 0;
}
