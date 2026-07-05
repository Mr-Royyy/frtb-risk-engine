cmake_minimum_required(VERSION 3.16)

project(frtb_lite_risk_engine
  VERSION 0.1.0
  LANGUAGES CXX
)

# C++20 is used because modern quant code benefits from stronger type support,
# clearer initialization, and better standard-library behavior.
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(BUILD_PYTHON_BINDINGS "Build optional pybind11 Python bindings" OFF)

add_library(frtb_lite_core
  src/portfolio.cpp
  src/var_engine.cpp
  src/es_engine.cpp
  src/stress_engine.cpp
  src/backtest_engine.cpp
  src/sensitivity_engine.cpp
  src/monte_carlo_engine.cpp
)

target_include_directories(frtb_lite_core
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

add_executable(frtb_lite_demo
  src/main.cpp
)

target_link_libraries(frtb_lite_demo
  PRIVATE
    frtb_lite_core
)

enable_testing()

add_executable(test_risk_engine
  tests/test_risk_engine.cpp
)

target_link_libraries(test_risk_engine
  PRIVATE
    frtb_lite_core
)

add_test(NAME risk_engine_unit_tests COMMAND test_risk_engine)

if(BUILD_PYTHON_BINDINGS)
  find_package(pybind11 CONFIG REQUIRED)

  pybind11_add_module(risk_engine_py
    ../python/bindings/risk_engine_pybind.cpp
  )

  target_link_libraries(risk_engine_py
    PRIVATE
      frtb_lite_core
  )
endif()

add_executable(monte_carlo_benchmark
  tools/monte_carlo_benchmark.cpp
)

target_link_libraries(monte_carlo_benchmark
  PRIVATE
    frtb_lite_core
)

target_include_directories(monte_carlo_benchmark
  PRIVATE
    include
)

find_package(Python COMPONENTS Interpreter Development REQUIRED)

execute_process(
  COMMAND ${Python_EXECUTABLE} -m pybind11 --cmakedir
  OUTPUT_VARIABLE pybind11_DIR
  OUTPUT_STRIP_TRAILING_WHITESPACE
)

find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(frtb_lite_cpp
  bindings/risk_engine_pybind.cpp
)

target_link_libraries(frtb_lite_cpp
  PRIVATE
    frtb_lite_core
)

target_include_directories(frtb_lite_cpp
  PRIVATE
    include
)