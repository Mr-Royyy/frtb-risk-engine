#include "monte_carlo_engine.hpp"


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

double MonteCarloEngine::compute_portfolio_variance(
    const std::vector<double>& exposures,
    const std::vector<std::vector<double>>& covariance) {
  const std::size_t factor_count = exposures.size();

  double variance = 0.0;

  for (std::size_t i = 0; i < factor_count; ++i) {
    for (std::size_t j = 0; j < factor_count; ++j) {
      variance += exposures[i] * covariance[i][j] * exposures[j];
    }
  }

  if (variance < -1e-8) {
    throw std::invalid_argument("Portfolio variance cannot be negative.");
  }

  return std::max(variance, 0.0);
}


std::vector<double> MonteCarloEngine::simulate_losses(
    const std::vector<double>& exposures,
    const std::vector<std::vector<double>>& covariance,
    std::size_t simulations,
    std::uint32_t seed) {
  validate_inputs(exposures, covariance, simulations);

  const double portfolio_variance = compute_portfolio_variance(exposures, covariance);
  const double portfolio_volatility = std::sqrt(portfolio_variance);

  std::mt19937 generator(seed);
  std::normal_distribution<double> portfolio_normal(0.0, portfolio_volatility);

  std::vector<double> losses;
  losses.reserve(simulations);

  for (std::size_t path = 0; path < simulations; ++path) {
    const double pnl = portfolio_normal(generator);
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

  if (losses.empty()) {
    throw std::invalid_argument("Monte Carlo loss vector cannot be empty.");
  }

  const std::size_t n = losses.size();

  std::size_t var_index = static_cast<std::size_t>(
      std::ceil(confidence * static_cast<double>(n))) - 1;

  if (var_index >= n) {
    var_index = n - 1;
  }

  // nth_element partially orders the vector so the VaR element is in the
  // correct sorted position, without fully sorting the entire loss vector.
  // This is faster than sorting all simulated losses when only the tail is
  // needed for VaR / ES.
  std::nth_element(losses.begin(), losses.begin() + var_index, losses.end());

  const double var_loss = losses[var_index];

  double tail_sum = 0.0;
  std::size_t tail_count = 0;

  for (const double loss : losses) {
    if (loss >= var_loss) {
      tail_sum += loss;
      ++tail_count;
    }
  }

  const double es_loss =
      tail_count > 0 ? tail_sum / static_cast<double>(tail_count) : var_loss;

  const double mean_loss =
      std::accumulate(losses.begin(), losses.end(), 0.0) /
      static_cast<double>(losses.size());

  return MonteCarloResult{
      var_loss,
      es_loss,
      mean_loss,
      simulations,
      tail_count,
  };
}
}  // namespace frtb_lite