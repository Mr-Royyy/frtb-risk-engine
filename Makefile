.PHONY: validate risk configure build test dashboard

validate:
	python python/data/validate_portfolio.py --portfolio sample_data/sample_portfolio.csv --factors sample_data/factor_mapping.csv

risk:
	python python/analytics/run_risk.py --portfolio sample_data/sample_portfolio.csv --prices sample_data/sample_prices.csv --factors sample_data/factor_mapping.csv --scenarios sample_data/stress_scenarios.yaml

configure:
	cmake -S cpp -B build

build:
	cmake --build build

test:
	ctest --test-dir build --output-on-failure

dashboard:
	streamlit run python/dashboard/app.py
