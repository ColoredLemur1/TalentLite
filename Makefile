.PHONY: check perf

check:
	ruff check .
	ruff format --check .
	pytest --cov=app --cov-report=term-missing

perf:
	pytest -m performance -s
