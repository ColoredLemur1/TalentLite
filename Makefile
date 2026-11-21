.PHONY: check perf audit

check:
	ruff check .
	ruff format --check .
	pytest --cov=app --cov-report=term-missing --cov-fail-under=80

perf:
	pytest -m performance -s

audit:
	pip-audit -r requirements.txt -r requirements-dev.txt
