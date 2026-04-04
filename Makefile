.PHONY: test lint format install dev clean

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements.txt -r requirements-test.txt

test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term

lint:
	ruff check .
	mypy . --ignore-missing-imports

format:
	ruff format .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache htmlcov .coverage
