.PHONY: check perf audit

check:
	ruff check .
	ruff format --check .
	pytest --cov=app --cov-report=term-missing

perf:
	pytest -m performance -s

audit:
	pip-audit -r requirements.txt -r requirements-dev.txt
