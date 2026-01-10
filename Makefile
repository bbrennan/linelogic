.PHONY: help setup install dev-install test test-cov lint format type-check clean run

help:
	@echo "LineLogic - Sports Prop Analytics System"
	@echo ""
	@echo "Available commands:"
	@echo "  make setup        - Initialize project (git, install deps, pre-commit)"
	@echo "  make install      - Install production dependencies"
	@echo "  make dev-install  - Install development dependencies"
	@echo "  make test         - Run test suite"
	@echo "  make test-cov     - Run tests with coverage report"
	@echo "  make lint         - Run ruff linter"
	@echo "  make format       - Format code with ruff"
	@echo "  make type-check   - Run mypy type checking"
	@echo "  make clean        - Remove build artifacts and cache"
	@echo "  make run          - Run CLI smoke test"

setup:
	@echo "Setting up LineLogic development environment..."
	git init
	uv venv
	uv pip install -e ".[dev]"
	pre-commit install
	@echo "Setup complete! Activate venv with: source .venv/bin/activate"

install:
	uv pip install -e .

dev-install:
	uv pip install -e ".[dev]"

test:
	pytest

test-cov:
	pytest --cov --cov-report=html --cov-report=term

lint:
	ruff check src tests

format:
	ruff format src tests
	ruff check --fix src tests

type-check:
	mypy src

clean:
	rm -rf build dist *.egg-info
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	rm -rf htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run:
	linelogic --help
