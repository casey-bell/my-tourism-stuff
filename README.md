# My Tourism Stuff
An analytical project.

## Project structure
```text
my-tourism-stuff/
├── .github/
│   └── workflows/
│       └── ci.yml                   # CI/CD pipeline configuration
├── data/
│   ├── interim/                     # Processed intermediate data
│   │   └── .gitkeep
│   └── raw/                         # Original source data (immutable)
│       └── overseas-visitors-to-britain-2024.xlsx
├── notebooks/
│   └── 01-ingest-and-clean.ipynb    # Exploratory data analysis and cleaning
├── src/                             # Source code package
│   ├── data/
│   │   ├── clean.py                 # Data cleaning functions
│   │   ├── load.py                  # Data loading utilities
│   │   ├── schemas.py               # Data structure definitions
│   │   ├── transform.py             # Data transformation logic
│   │   └── validate.py              # Data validation functions
│   ├── utils/
│   │   └── io.py                    # I/O utility functions
│   ├── config.py                    # Project configuration
│   └── pipeline.py                  # Main pipeline orchestration
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
- Expenditure (£ millions)
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

## Quick start

### Installation
```bash
# Install project dependencies
pip install -e .
```

### Running the pipeline
```bash
# Execute the complete data processing pipeline
make all
```

### Manual execution
For exploratory analysis or development:
```bash
# Run the Jupyter notebook
jupyter notebook notebooks/01-ingest-and-clean.ipynb
```
```bash
# Or run the pipeline directly from src
python src/pipeline.py
```

## Development

### Testing
```bash
# Run the test suite
python -m pytest tests/
```
```bash
# Run tests with CI configuration
python -m pytest tests/ --cov=src
```

### CI/CD
The project uses GitHub Actions for continuous integration. The workflow runs on pushes and pull requests to the main branch, executing:
- Test suite with pytest
- Code coverage reporting
- Dependency caching

### Available Make commands
```bash
make all          # Run complete pipeline
make data         # Process data only
make clean        # Clean generated files
make help         # Show available commands
```

## Data pipeline
The project implements a reproducible data processing workflow:
- Extract: Raw data from ONS Excel files
- Transform: Clean, validate, and reshape data using modular components
- Load: Output analysis-ready datasets to data/interim/
- Validate: Data quality checks and schema validation
- Test: Comprehensive test coverage for data operations

## Data source and licensing
- Data source: Office for National Statistics
- Data licence: Crown copyright, Open Government Licence v3.0
- Code licence: MIT License (see LICENSE file)

## Contact

### Project maintainer
- Name: Casey Bell
- Email: casey.bell.7@outlook.com
- LinkedIn: [linkedin.com/in/casey-bell](linkedin.com/in/casey-bell)

### Official data enquiries
- Office for National Statistics
- Email: pop.info@ons.gov.uk

## Contributing
This project follows standard data science best practices:
- Raw data is kept immutable in `data/raw/`
- All data processing is scripted and reproducible
- Intermediate data outputs are stored separately
- Dependencies are explicitly managed
- Comprehensive test suite for data processing logic
- Modular code organisation with separate concerns
- Continuous integration for automated testing
