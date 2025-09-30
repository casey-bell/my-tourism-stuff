# Makefile for my-tourism-stuff

# Configuration
PYTHON := python3
PIP := $(PYTHON) -m pip
NOTEBOOK_DIR := notebooks
DATA_RAW_DIR := data/raw
DATA_INTERIM_DIR := data/interim
SRC_DIR := src
TESTS_DIR := tests

# Files
RAW_DATA := $(DATA_RAW_DIR)/overseas-visitors-to-britain-2024.xlsx
PIPELINE := pipeline.py

.PHONY: help install install-dev setup data pipeline notebook test lint type-check format clean clean-all all

help:
	@echo "UK Tourism Data Pipeline - Available targets:"
	@echo "  all        Run the complete data pipeline (default)"
	@echo "  install    Install production dependencies"
	@echo "  install-dev Install development dependencies"
	@echo "  setup      Set up development environment (install-dev + pre-commit)"
	@echo "  data       Process data (run pipeline + notebook)"
	@echo "  pipeline   Run the main data processing pipeline"
	@echo "  notebook   Execute the analysis notebook"
	@echo "  test       Run tests with coverage"
	@echo "  lint       Check code quality with flake8"
	@echo "  type-check Run static type checking with mypy"
	@echo "  format     Format code with black and isort"
	@echo "  clean      Remove Python cache and temporary files"
	@echo "  clean-all  Remove all generated files and outputs"

all: pipeline notebook

install:
	$(PIP) install --upgrade pip
	$(PIP) install -e .
	@echo "✅ Production dependencies installed"

install-dev:
	$(PIP) install --upgrade pip
	$(PIP) install -e .[dev]
	@echo "✅ Development dependencies installed"

setup: install-dev
	$(PYTHON) -m pre_commit install
	@echo "✅ Development environment setup complete"

data: pipeline notebook

pipeline: $(RAW_DATA)
	@echo "🚀 Running data processing pipeline..."
	$(PYTHON) $(PIPELINE)
	@echo "✅ Data pipeline complete"

notebook: $(RAW_DATA)
	@echo "📓 Executing analysis notebook..."
	$(PYTHON) -m jupyter nbconvert --to notebook --execute \
		--output $(NOTEBOOK_DIR)/01-ingest-and-clean-executed \
		$(NOTEBOOK_DIR)/01-ingest-and-clean.ipynb
	@echo "✅ Notebook execution complete"

test:
	@echo "🧪 Running tests..."
	$(PYTHON) -m pytest $(TESTS_DIR) -v --cov=$(SRC_DIR) --cov-report=term-missing
	@echo "✅ Tests complete"

lint:
	@echo "🔍 Checking code quality..."
	$(PYTHON) -m flake8 $(SRC_DIR) --max-line-length=88
	@echo "✅ Code quality check passed"

type-check:
	@echo "📝 Running type checks..."
	$(PYTHON) -m mypy $(SRC_DIR)
	@echo "✅ Type checking complete"

format:
	@echo "🎨 Formatting code..."
	$(PYTHON) -m black $(SRC_DIR) $(NOTEBOOK_DIR) $(PIPELINE)
	$(PYTHON) -m isort $(SRC_DIR) $(NOTEBOOK_DIR) $(PIPELINE)
	@echo "✅ Code formatted"

clean:
	@echo "🧹 Cleaning temporary files..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .coverage htmlcov .cache build dist
	@echo "✅ Cleaned temporary files"

clean-all: clean
	@echo "🗑️  Removing generated data..."
	@rm -rf $(DATA_INTERIM_DIR)
	@rm -f $(NOTEBOOK_DIR)/*-executed.ipynb
	@rm -f $(NOTEBOOK_DIR)/*.html
	@echo "✅ Removed all generated outputs"

# Development workflow targets
dev: install-dev setup
	@echo "🚀 Development environment ready!"

check: lint type-check test
	@echo "✅ All checks passed!"

# Default target
.DEFAULT_GOAL := all
