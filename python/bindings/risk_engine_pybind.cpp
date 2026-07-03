/**
 * Optional pybind11 binding starter.
 *
 * Build this only after pybind11 is installed and CMake is called with:
 *
 *   cmake -S cpp -B build -DBUILD_PYTHON_BINDINGS=ON
 *
 * The starter binding exposes VaR and Expected Shortfall calculators. Future
 * milestones can expose Portfolio, StressEngine, BacktestEngine, and the full
 * risk run workflow.
 */

#include "es_engine.hpp"
#include "var_engine.hpp"

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

PYBIND11_MODULE(risk_engine_py, module) {
  module.doc() = "Python bindings for the FRTB-Lite C++ risk engine.";

  module.def(
      "historical_var",
      &frtb_lite::VarEngine::historical_var,
      py::arg("losses"),
      py::arg("confidence"),
      "Calculate historical VaR from a vector of positive losses.");

  module.def(
      "historical_es",
      &frtb_lite::ExpectedShortfallEngine::historical_es,
      py::arg("losses"),
      py::arg("confidence"),
      "Calculate historical Expected Shortfall from positive losses.");
}
