# Makefile for my-tourism-stuff

# Configuration
PYTHON := python3
NOTEBOOK_DIR := notebooks
DATA_RAW_DIR := data/raw
DATA_PROC_DIR := data/processed
SRC_DIR := src

# Files
RAW_DATA := $(DATA_RAW_DIR)/overseas-visitors-to-britain-2024.xlsx
NOTEBOOK := $(NOTEBOOK_DIR)/01-ingest-and-clean.ipynb

.PHONY: help install test lint format clean data clean-all

help:
	@echo "UK Tourism Data Analysis - Available targets:"
	@echo "  install    Install dependencies from pyproject.toml"
	@echo "  data       Run data ingestion and cleaning notebook"
	@echo "  test       Run tests (if any)"
	@echo "  lint       Check code quality with flake8"
	@echo "  format     Format code with black and isort"
	@echo "  clean      Remove Python cache and temporary files"
	@echo "  clean-all  Remove all generated files and outputs"

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .[dev]
	@echo "✅ Dependencies installed"

data: $(RAW_DATA)
	@echo "🚀 Running data ingestion pipeline..."
	$(PYTHON) -m jupyter nbconvert --to notebook --execute \
		--output $(NOTEBOOK_DIR)/01-ingest-and-clean-executed \
		$(NOTEBOOK)
	@echo "✅ Data processing complete"

test:
	@if [ -d "$(SRC_DIR)" ] && [ -n "$$(ls -A $(SRC_DIR) 2>/dev/null)" ]; then \
		$(PYTHON) -m pytest $(SRC_DIR) -v; \
	else \
		echo "⚠️  No tests configured - add tests to $(SRC_DIR)"; \
	fi

lint:
	$(PYTHON) -m flake8 $(SRC_DIR) --max-line-length=88
	@echo "✅ Code quality check passed"

format:
	$(PYTHON) -m black $(SRC_DIR) $(NOTEBOOK_DIR)
	$(PYTHON) -m isort $(SRC_DIR) $(NOTEBOOK_DIR)
	@echo "✅ Code formatted"

clean:
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .pytest_cache .coverage htmlcov
	@echo "✅ Cleaned temporary files"

clean-all: clean
	@rm -rf $(DATA_PROC_DIR)
	@rm -f $(NOTEBOOK_DIR)/*-executed.ipynb
	@echo "✅ Removed all generated outputs"

# Default target
.DEFAULT_GOAL := help
