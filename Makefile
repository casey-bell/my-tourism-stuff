# Makefile for my-tourism-stuff

# Paths
PYTHON        := python3
NBEXEC        := jupyter nbconvert
ROOT          := $(PWD)
NOTEBOOKS_DIR := notebooks
RAW_DIR       := data/raw
PROC_DIR      := data/processed
FIG_DIR       := figures
REPORTS_DIR   := reports

# Data
DATA_XLSX := overseas-visitors-to-britain-2024.xlsx

# Default
.PHONY: help
help:
    @echo "Available targets:"
    @echo "  init        Create directories and place raw data"
    @echo "  env         Set up Python environment and install project"
    @echo "  ingest      Execute ingestion/cleaning notebook"
    @echo "  validate    Basic checks on processed outputs"
    @echo "  eda         Execute EDA notebook (if present)"
    @echo "  report      Build summary report (if present)"
    @echo "  figures     Collate figures (created during EDA)"
    @echo "  clean       Remove generated outputs"
    @echo "  clobber     Reset repo-generated artefacts"

# Setup
.PHONY: init
init:
    @mkdir -p $(RAW_DIR) $(PROC_DIR) $(FIG_DIR) $(REPORTS_DIR)
    @test -f "$(DATA_XLSX)" && cp "$(DATA_XLSX)" "$(RAW_DIR)/" || \
        ( echo "Missing $(DATA_XLSX) in repo root"; exit 1 )
    @echo "Initialised directories and staged raw data."

.PHONY: env
env:
    $(PYTHON) -m pip install -U pip
    # Install project from pyproject.toml (editable)
    $(PYTHON) -m pip install -e .
    # Core tooling for notebooks
    $(PYTHON) -m pip install jupyter nbconvert
    @echo "Environment ready."

# Ingestion and cleaning
.PHONY: ingest
ingest: init
    # Execute the ingestion/cleaning notebook and save executed copy
    $(NBEXEC) --to notebook --execute \
        "$(NOTEBOOKS_DIR)/01-ingest-and-clean.ipynb" \
        --output "$(NOTEBOOKS_DIR)/01-ingest-and-clean-executed.ipynb"
    @echo "Ingestion and cleaning completed."

# Validation
.PHONY: validate
validate: ingest
    @test -d "$(PROC_DIR)" || ( echo "Processed directory missing"; exit 1 )
    @ls "$(PROC_DIR)" | grep -E 'csv$$' > /dev/null || \
        ( echo "No processed CSVs found in $(PROC_DIR)"; exit 1 )
    @echo "Validation passed: processed CSVs present."

# Exploratory analysis
.PHONY: eda
eda: ingest
    @test -f "$(NOTEBOOKS_DIR)/02-eda-and-trends.ipynb" || \
        ( echo "EDA notebook not found: $(NOTEBOOKS_DIR)/02-eda-and-trends.ipynb"; exit 1 )
    $(NBEXEC) --to notebook --execute \
        "$(NOTEBOOKS_DIR)/02-eda-and-trends.ipynb" \
        --output "$(NOTEBOOKS_DIR)/02-eda-and-trends-executed.ipynb"
    @echo "EDA completed."

# Reports
.PHONY: report
report: eda
    @test -f "$(REPORTS_DIR)/gb-tourism-2019-2024-summary.md" || \
        ( echo "Report source missing: $(REPORTS_DIR)/gb-tourism-2019-2024-summary.md"; exit 1 )
    @echo "Report ready: $(REPORTS_DIR)/gb-tourism-2019-2024-summary.md"

# Figures
.PHONY: figures
figures: eda
    @test -d "$(FIG_DIR)" || ( echo "Figures directory missing"; exit 1 )
    @echo "Figures available in $(FIG_DIR)."

# Cleaning
.PHONY: clean
clean:
    @rm -rf "$(PROC_DIR)" "$(FIG_DIR)" "$(REPORTS_DIR)"
    @mkdir -p "$(PROC_DIR)" "$(FIG_DIR)" "$(REPORTS_DIR)"
    @echo "Cleaned generated outputs."

.PHONY: clobber
clobber: clean
    @rm -rf "$(RAW_DIR)"
    @rm -f "$(NOTEBOOKS_DIR)/01-ingest-and-clean-executed.ipynb"
    @rm -f "$(NOTEBOOKS_DIR)/02-eda-and-trends-executed.ipynb"
    @echo "Reset repository-generated artefacts."
