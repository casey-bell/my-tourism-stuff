# Makefile for my-tourism-stuff

# Configuration
PYTHON := python3
POETRY := poetry
PYTEST := $(PYTHON) -m pytest
MYPY := $(PYTHON) -m mypy
BLACK := $(PYTHON) -m black
ISORT := $(PYTHON) -m isort
FLAKE8 := $(PYTHON) -m flake8
JUPYTER := $(PYTHON) -m jupyter

# Paths
NOTEBOOK_DIR := notebooks
DATA_RAW_DIR := data/raw
DATA_INTERIM_DIR := data/interim
SRC_DIR := src
TESTS_DIR := tests

# Targets
.PHONY: help install install-dev lock test lint type-check format clean clean-all data pipeline notebook check

help:
	@echo "UK Tourism Data Pipeline"
	@echo "Available targets:"
	@echo "  install     Install production dependencies"
	@echo "  install-dev Install development dependencies"
	@echo "  lock        Update lock file"
	@echo "  test        Run tests"
	@echo "  lint        Check code style"
	@echo "  type-check  Run static type checking"
	@echo "  format      Format code"
	@echo "  check       Run all checks (lint + type-check + test)"
	@echo "  data        Process data through pipeline"
	@echo "  pipeline    Run data processing pipeline"
	@echo "  notebook    Execute analysis notebook"
	@echo "  clean       Remove temporary files"
	@echo "  clean-all   Remove all generated files"

install:
	$(POETRY) install --only main

install-dev:
	$(POETRY) install --with dev

lock:
	$(POETRY) lock --no-update

test:
	$(POETRY) run $(PYTEST) $(TESTS_DIR) --cov=$(SRC_DIR) --cov-report=term-missing

lint:
	$(POETRY) run $(FLAKE8) $(SRC_DIR) $(TESTS_DIR) --max-line-length=88 --extend-ignore=E203,W503
	$(POETRY) run $(BLACK) $(SRC_DIR) $(TESTS_DIR) --check --diff
	$(POETRY) run $(ISORT) $(SRC_DIR) $(TESTS_DIR) --check --diff

type-check:
	$(POETRY) run $(MYPY) $(SRC_DIR) $(TESTS_DIR)

format:
	$(POETRY) run $(BLACK) $(SRC_DIR) $(TESTS_DIR)
	$(POETRY) run $(ISORT) $(SRC_DIR) $(TESTS_DIR)

check: lint type-check test

data: pipeline notebook

pipeline:
	$(POETRY) run $(PYTHON) -m src.pipeline

notebook:
	$(POETRY) run $(JUPYTER) nbconvert --execute --inplace $(NOTEBOOK_DIR)/01-ingest-and-clean.ipynb

clean:
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.ipynb_checkpoints" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .coverage htmlcov .cache build dist

clean-all: clean
	@rm -rf $(DATA_INTERIM_DIR)/*
	@find $(NOTEBOOK_DIR) -name "*-executed.ipynb" -delete
	@find $(NOTEBOOK_DIR) -name "*.html" -delete

.DEFAULT_GOAL := help
