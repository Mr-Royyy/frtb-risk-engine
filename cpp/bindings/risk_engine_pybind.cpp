#include "monte_carlo_engine.hpp"

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

/**
 * Python bindings for the FRTB-Lite C++ risk engine.
 *
 * This module exposes the optimized C++ Monte Carlo VaR / Expected Shortfall
 * engine to Python. The intended architecture is:
 *
 * - C++ handles computationally intensive risk calculations.
 * - Python handles analytics workflow, reporting, validation, and dashboard UI.
 */
PYBIND11_MODULE(frtb_lite_cpp, module) {
  module.doc() = "Python bindings for the FRTB-Lite C++ market-risk engine";

  py::class_<frtb_lite::MonteCarloResult>(module, "MonteCarloResult")
      .def_readonly("var_loss", &frtb_lite::MonteCarloResult::var_loss)
      .def_readonly(
          "expected_shortfall",
          &frtb_lite::MonteCarloResult::expected_shortfall)
      .def_readonly("mean_loss", &frtb_lite::MonteCarloResult::mean_loss)
      .def_readonly("simulations", &frtb_lite::MonteCarloResult::simulations)
      .def_readonly(
          "tail_observations",
          &frtb_lite::MonteCarloResult::tail_observations);

  module.def(
      "simulate_losses",
      &frtb_lite::MonteCarloEngine::simulate_losses,
      py::arg("exposures"),
      py::arg("covariance"),
      py::arg("simulations"),
      py::arg("seed") = 42,
      "Simulate portfolio losses using the optimized C++ Monte Carlo engine.");

  module.def(
      "calculate_var_es",
      &frtb_lite::MonteCarloEngine::calculate_var_es,
      py::arg("exposures"),
      py::arg("covariance"),
      py::arg("confidence"),
      py::arg("simulations"),
      py::arg("seed") = 42,
      "Calculate Monte Carlo VaR and Expected Shortfall using the optimized C++ engine.");
}