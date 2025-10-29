# My Tourism Stuff

[![CI pipeline](https://github.com/casey-bell/my-tourism-stuff/actions/workflows/ci.yml/badge.svg)](https://github.com/casey-bell/my-tourism-stuff/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A data analysis pipeline for processing and analysing UK tourism statistics from the Office for National Statistics (ONS). This project provides reproducible ETL workflows, data validation, and analytical capabilities for exploring overseas visitor trends to Great Britain.

## Table of Contents
- [Features](#features)
- [Project Structure](#project-structure)
- [Dataset](#dataset)
- [Quick Start](#quick-start)
- [Development](#development)
- [Data Pipeline](#data-pipeline)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Technical Requirements](#technical-requirements)
- [Data Source and Licensing](#data-source-and-licensing)
- [Contact](#contact)
- [Contributing](#contributing)
- [Acknowledgments](#acknowledgments)

## Features

- **Reproducible ETL pipeline**: Fully scripted data processing from raw Excel files to analysis-ready datasets
- **Data validation**: Schema enforcement and quality checks throughout the pipeline
- **Modular architecture**: Separate components for loading, cleaning, transforming, and validating data
- **Comprehensive testing**: Full test coverage for data operations with pytest
- **Interactive analysis**: Jupyter notebooks for exploratory data analysis
- **CI/CD integration**: Automated testing and deployment via GitHub Actions
- **Multiple data formats**: Support for Excel, CSV, and Parquet formats
- **Command-line interface**: Easy pipeline execution and data management via CLI

## Project Structure
```text
my-tourism-stuff/
├── .github/
│   └── workflows/
│       ├── ci.yml                   # Continuous integration testing
│       ├── deploy.yml               # Deployment pipeline
│       └── lint.yml                 # Code quality checks
├── data/
│   ├── interim/                     # Processed intermediate data
│   │   └── visitors_by_quarter.csv
│   ├── processed/                   # Analysis-ready datasets
│   │   └── visitors_quarterly.parquet
│   └── raw/                         # Original source data (immutable)
│       └── overseas-visitors-to-britain-2024.xlsx
├── notebooks/
│   ├── 01-ingest-and-clean.ipynb        # Data ingestion and cleaning
│   └── 02-transform-and-validate.ipynb  # Data transformation and validation
├── src/                             # Source code package
│   ├── data/
│   │   ├── clean.py                 # Data cleaning functions
│   │   ├── load.py                  # Data loading utilities
│   │   ├── schemas.py               # Data structure definitions
│   │   ├── transform.py             # Data transformation logic
│   │   └── validate.py              # Data validation functions
│   ├── utils/
│   │   └── io.py                    # I/O utility functions
│   ├── cli.py                       # Command-line interface
│   ├── config.py                    # Project configuration
│   └── pipeline.py                  # Pipeline orchestration
├── tests/                           # Test suite
│   ├── test_clean.py
│   ├── test_load.py
│   ├── test_transform.py
│   └── test_validate.py
├── .gitignore
├── LICENSE
├── Makefile                         # Automation commands
├── pyproject.toml                   # Project dependencies and configuration
└── README.md
```

## Dataset
- Source: Office for National Statistics (ONS)
- File: `data/raw/overseas-visitors-to-britain-2024.xlsx`

### Data characteristics
- Period: Q1 2019 to Q4 2024 (quarterly)
- Coverage: UK (2019–2023) → Great Britain (2024 onwards)

### Key metrics
- Number of visits (thousands)
- Expenditure (£ million)
- Nights stayed (thousands)

### Data breakdowns
- Geography: North America, Europe, Other Countries
- Purpose: Holiday, Business, Visiting Friends and Relatives (VFR), Miscellaneous
- Transport: Air, sea and tunnel
- UK regions: All major UK regions visited
- Countries: Individual countries of residence

### Important notes
- Methodological break: Data from 2024 onwards covers Great Britain only (excluding Northern Ireland).
- Developmental statistics: These estimates are labelled as developmental whilst ONS methodologies are being refined.
- Analysis should account for the 2024 methodological break with appropriate handling.

## Quick Start

### Prerequisites

- **Python 3.9 or higher** (check with `python --version`)
- **pip** package manager
- **Poetry** (optional, for dependency management - see [Poetry installation](https://python-poetry.org/docs/#installation))
- **Git** for version control

### Installation

#### Option 1: Using pip (recommended for users)

```bash
# Clone the repository
git clone https://github.com/casey-bell/my-tourism-stuff.git
cd my-tourism-stuff

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the project and its dependencies
pip install -e .
```

#### Option 2: Using Poetry (recommended for developers)

```bash
# Clone the repository
git clone https://github.com/casey-bell/my-tourism-stuff.git
cd my-tourism-stuff

# Install dependencies using Poetry
poetry install

# Activate the Poetry virtual environment
poetry shell
```

### Running the Pipeline

```bash
# Execute the complete data processing pipeline
make all
```

Or using Poetry:

```bash
poetry run make all
```

### Manual Execution

For exploratory analysis or development:

```bash
# Run Jupyter notebooks
jupyter notebook notebooks/
```

```bash
# Or run the pipeline via CLI
python -m src.cli run
```

```bash
# List available CLI commands
python -m src.cli --help
```

## Development

### Setting Up Development Environment

```bash
# Install development dependencies
poetry install --with dev

# Or with pip
pip install -e ".[dev]"
```

### Testing

```bash
# Run the test suite
pytest tests/
```

```bash
# Run tests with coverage as per CI configuration
pytest tests/ --cov=src --cov-report=term-missing
```

```bash
# Run tests using Make (with Poetry)
make test
```

### Code Quality

```bash
# Format code with black and isort
make format

# Check code style (lint)
make lint

# Run static type checking
make type-check

# Run all checks (lint + type-check + test)
make check
```

### CI/CD

The project uses GitHub Actions for continuous integration. On pushes and pull requests to the main branch, it runs:

- **Test suite** with pytest
- **Code coverage** reporting
- **Code quality** linting (flake8, black, isort)
- **Type checking** with mypy
- **Deployment** checks
- **Dependency caching** for faster builds

### Available Make Commands

```bash
make help         # Show all available commands
make install      # Install production dependencies
make install-dev  # Install development dependencies
make test         # Run tests with coverage
make lint         # Check code style
make type-check   # Run static type checking
make format       # Auto-format code
make check        # Run all checks
make all          # Run complete pipeline
make data         # Process data only
make pipeline     # Run data processing pipeline
make notebook     # Execute analysis notebooks
make clean        # Clean temporary files
make clean-all    # Clean all generated files
```

## Data Pipeline

A reproducible data processing workflow:

1. **Extract**: Raw data from ONS Excel files in `data/raw/`
2. **Transform**: Clean, validate and reshape data using modular components
3. **Load**: Output intermediate data to `data/interim/` and final datasets to `data/processed/`
4. **Validate**: Data quality checks and schema validation in `src/data/validate.py`
5. **Test**: Comprehensive test coverage for data operations in `tests/`

### Data Flow

```
Raw Excel data → Interim CSV (for inspection) → Processed Parquet (for analysis)
```

- All data processing is **scripted and reproducible**
- **Schema enforcement** through `src/data/schemas.py`
- **Separation of concerns**: raw, interim, and processed data directories

## Examples

### Running Individual Pipeline Steps

```bash
# Load and process data only
python -m src.cli process-data

# Run data validation
python -m src.cli validate

# Run data transformation
python -m src.cli transform

# List all data files and their sizes
python -m src.cli ls-data
```

### Using Jupyter Notebooks

```bash
# Start Jupyter Lab
jupyter lab

# Navigate to notebooks/ directory
# Open and run:
# - 01-ingest-and-clean.ipynb
# - 02-transform-and-validate.ipynb
```

### Programmatic Access

```python
from src.data import load, transform, validate

# Load raw data
data = load.load_raw_data()

# Transform data
transformed = transform.transform(data)

# Validate output
validate.validate_schema(transformed)
```

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'src'`
- **Solution**: Ensure you've installed the package with `pip install -e .` and are in the project root directory

**Issue**: `FileNotFoundError` when running pipeline
- **Solution**: Ensure the raw data file exists in `data/raw/overseas-visitors-to-britain-2024.xlsx`

**Issue**: Poetry command not found
- **Solution**: Install Poetry following [official instructions](https://python-poetry.org/docs/#installation) or use pip-based installation instead

**Issue**: Tests failing with import errors
- **Solution**: Reinstall the package in editable mode: `pip install -e .`

**Issue**: Notebook kernel not found
- **Solution**: Install Jupyter in your virtual environment: `pip install jupyter jupyterlab`

### Getting Help

If you encounter issues not covered here:
1. Check the [Issues page](https://github.com/casey-bell/my-tourism-stuff/issues) for similar problems
2. Run `make help` to see all available commands
3. Enable debug logging: `python -m src.cli run --debug`

## Technical Requirements

- **Python**: 3.9 or higher (see `pyproject.toml` for exact version requirements)
- **Operating System**: Linux, macOS, or Windows (with WSL recommended)
- **Memory**: Minimum 4GB RAM recommended for data processing
- **Storage**: ~500MB for repository and dependencies

### Core Dependencies

- pandas (>=2.1.0) - Data manipulation
- numpy (>=1.24.0) - Numerical computing
- openpyxl (>=3.1.0) - Excel file reading
- pytest (>=7.4.0) - Testing framework
- jupyter (>=1.0.0) - Interactive notebooks

All dependencies are managed via `pyproject.toml`. For the complete list, see the project configuration file.

## Data Source and Licensing

### Data Source

- **Provider**: Office for National Statistics (ONS)
- **Dataset**: Overseas Visitors to Britain
- **File**: `data/raw/overseas-visitors-to-britain-2024.xlsx`
- **Update Frequency**: Quarterly
- **Official Source**: [ONS Travel and Tourism Statistics](https://www.ons.gov.uk/)

### Licensing

- **Data License**: Crown copyright, [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)
- **Code License**: MIT License (see `LICENSE` file)

### Citation

If you use this project or the processed datasets, please cite:

```
Office for National Statistics (2024). Overseas Visitors to Britain.
Retrieved from: https://www.ons.gov.uk/

Data processing pipeline: Casey Bell (2025). my-tourism-stuff.
Available at: https://github.com/casey-bell/my-tourism-stuff
```

## Contact

### Project maintainer
- Name: Casey Bell
- Email: [casey.bell.7@outlook.com](mailto:casey.bell.7@outlook.com)
- LinkedIn: [casey-bell](https://linkedin.com/in/casey-bell)

### Official data enquiries
- Office for National Statistics
- Email: [pop.info@ons.gov.uk](mailto:pop.info@ons.gov.uk)

## Contributing

Contributions are welcome! This project follows standard data science best practices:

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Set up** your development environment:
   ```bash
   poetry install --with dev
   # or
   pip install -e ".[dev]"
   ```
4. **Make** your changes following the code style guidelines
5. **Test** your changes:
   ```bash
   make check  # Runs lint, type-check, and tests
   ```
6. **Commit** your changes (`git commit -m 'Add amazing feature'`)
7. **Push** to your branch (`git push origin feature/amazing-feature`)
8. **Open** a Pull Request

### Code Style Guidelines

- Follow **PEP 8** conventions
- Use **black** for code formatting (line length: 88)
- Use **isort** for import sorting
- Add **type hints** where appropriate
- Write **docstrings** for functions and classes
- Maintain test coverage above 80%

### Project Principles

- **Raw data is immutable**: Never modify files in `data/raw/`
- **All processing is scripted**: No manual data manipulation
- **Reproducibility**: Anyone should be able to run the pipeline and get the same results
- **Testing**: All data processing logic must have corresponding tests
- **Documentation**: Update README and docstrings when adding features
- **Modular design**: Keep functions focused and reusable

### Areas for Contribution

- Adding new data sources or datasets
- Improving data validation logic
- Adding new analytical notebooks
- Enhancing visualizations
- Improving documentation
- Adding more comprehensive tests
- Performance optimizations

## Acknowledgments

- **Office for National Statistics (ONS)** for providing open access to UK tourism data
- **Python community** for the excellent data science ecosystem
- **Contributors** who have helped improve this project
Special thanks to:
- The pandas development team for their powerful data manipulation library
- The pytest team for the comprehensive testing framework
