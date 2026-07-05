#include "monte_carlo_engine.hpp"

#include "es_engine.hpp"
#include "var_engine.hpp"

#include <algorithm>
#include <cmath>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

namespace frtb_lite {

void MonteCarloEngine::validate_inputs(
    const std::vector<double>& exposures,
    const std::vector<std::vector<double>>& covariance,
    std::size_t simulations) {
  if (exposures.empty()) {
    throw std::invalid_argument("Monte Carlo exposures cannot be empty.");
  }

  if (covariance.empty()) {
    throw std::invalid_argument("Monte Carlo covariance matrix cannot be empty.");
  }

  if (simulations == 0) {
    throw std::invalid_argument("Monte Carlo simulations must be greater than zero.");
  }

  const std::size_t factor_count = exposures.size();

  if (covariance.size() != factor_count) {
    throw std::invalid_argument("Covariance row count must match exposure count.");
  }

  for (const auto& row : covariance) {
    if (row.size() != factor_count) {
      throw std::invalid_argument("Covariance matrix must be square.");
    }
  }
}

std::vector<std::vector<double>> MonteCarloEngine::cholesky_decompose(
    const std::vector<std::vector<double>>& matrix) {
  const std::size_t n = matrix.size();
  std::vector<std::vector<double>> lower(n, std::vector<double>(n, 0.0));

  for (std::size_t row = 0; row < n; ++row) {
    for (std::size_t col = 0; col <= row; ++col) {
      double sum = 0.0;

      for (std::size_t k = 0; k < col; ++k) {
        sum += lower[row][k] * lower[col][k];
      }

      if (row == col) {
        const double diagonal_value = matrix[row][row] - sum;

        if (diagonal_value < -1e-12) {
          throw std::invalid_argument(
              "Covariance matrix is not positive semi-definite.");
        }

        lower[row][col] = std::sqrt(std::max(diagonal_value, 1e-12));
      } else {
        if (std::fabs(lower[col][col]) < 1e-12) {
          lower[row][col] = 0.0;
        } else {
          lower[row][col] = (matrix[row][col] - sum) / lower[col][col];
        }
      }
    }
  }

  return lower;
}

std::vector<double> MonteCarloEngine::simulate_losses(
    const std::vector<double>& exposures,
    const std::vector<std::vector<double>>& covariance,
    std::size_t simulations,
    std::uint32_t seed) {
  validate_inputs(exposures, covariance, simulations);

  const std::size_t factor_count = exposures.size();
  const auto lower = cholesky_decompose(covariance);

  std::mt19937 generator(seed);
  std::normal_distribution<double> standard_normal(0.0, 1.0);

  std::vector<double> losses;
  losses.reserve(simulations);

  for (std::size_t path = 0; path < simulations; ++path) {
    std::vector<double> independent_normals(factor_count, 0.0);
    std::vector<double> correlated_returns(factor_count, 0.0);

    for (std::size_t i = 0; i < factor_count; ++i) {
      independent_normals[i] = standard_normal(generator);
    }

    for (std::size_t row = 0; row < factor_count; ++row) {
      double value = 0.0;

      for (std::size_t col = 0; col <= row; ++col) {
        value += lower[row][col] * independent_normals[col];
      }

      correlated_returns[row] = value;
    }

    double pnl = 0.0;

    for (std::size_t i = 0; i < factor_count; ++i) {
      pnl += exposures[i] * correlated_returns[i];
    }

    losses.push_back(-pnl);
  }

  return losses;
}

MonteCarloResult MonteCarloEngine::calculate_var_es(
    const std::vector<double>& exposures,
    const std::vector<std::vector<double>>& covariance,
    double confidence,
    std::size_t simulations,
    std::uint32_t seed) {
  if (confidence <= 0.0 || confidence >= 1.0) {
    throw std::invalid_argument("Monte Carlo confidence must be between 0 and 1.");
  }

  std::vector<double> losses = simulate_losses(
      exposures,
      covariance,
      simulations,
      seed);

  const double var_loss = VarEngine::historical_var(losses, confidence);
  const double es_loss = ExpectedShortfallEngine::historical_es(losses, confidence);

  const double mean_loss =
      std::accumulate(losses.begin(), losses.end(), 0.0) /
      static_cast<double>(losses.size());

  const auto tail_count = static_cast<std::size_t>(
      std::count_if(
          losses.begin(),
          losses.end(),
          [var_loss](double loss) {
            return loss >= var_loss;
          }));

  return MonteCarloResult{
      var_loss,
      es_loss,
      mean_loss,
      simulations,
      tail_count,
  };
}

}  // namespace frtb_lite