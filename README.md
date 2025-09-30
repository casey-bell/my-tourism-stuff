# My Tourism Stuff
An analytical project.

## Project Structure
```text
my-tourism-stuff/
├── data/
│   ├── interim/                     # Processed intermediate data
│   └── raw/                         # Original source data (immutable)
├── notebooks/
│   └── 01-ingest-and-clean.ipynb    # Exploratory data analysis & cleaning
├── src/                             # Source code package
│   └── data/
│       ├── clean.py                 # Data cleaning functions
│       ├── load.py                  # Data loading utilities
│       └── transform.py             # Data transformation logic
├── pipeline.py                      # Main pipeline orchestration
├── Makefile                         # Automation commands
├── pyproject.toml                   # Project dependencies and configuration
├── README.md
├── LICENSE
└── .gitignore
```

## Dataset
- Source: [Office for National Statistics (ONS)](https://www.ons.gov.uk)  
- File: `data/raw/overseas-visitors-to-britain-2024.xlsx`

### Data Characteristics
- Period: Q1 2019 to Q4 2024 (quarterly)
- Coverage: UK (2019–2023) → Great Britain (2024 onwards)
- Key metrics:
  - Number of visits (thousands)
  - Expenditure (£ millions)
  - Nights stayed (thousands)

### Data Breakdowns
- Geography: North America, Europe, Other Countries
- Purpose: Holiday, Business, VFR (Visiting Friends & Relatives), Miscellaneous
- Transport: Air, Sea, and Tunnel
- UK regions: All major UK regions visited
- Countries: Individual countries of residence

### Important Notes
- Methodological break: Data from 2024 onwards covers Great Britain only (excluding Northern Ireland)
- Developmental statistics: These estimates are labelled as developmental while ONS methodologies are being refined

## Quick Start
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
# Or run the pipeline directly
python pipeline.py
```

## Usage Examples
- Tourism trend analysis: Identify seasonal patterns and long‑term trends
- Regional impact studies: Analyse economic impact across UK regions
- Market research: Understand visitor behaviour by country of residence
- Transportation planning: Inform infrastructure based on transport mode preferences

## Development
### Dependencies
Managed via `pyproject.toml` using modern Python packaging standards.

### Available Make commands
```bash
make all          # Run complete pipeline
make data         # Process data only
make clean        # Clean generated files
make help         # Show available commands
```

### Data Pipeline
The project implements a reproducible data processing workflow:
- Extract: Raw data from ONS Excel files
- Transform: Clean, validate, and reshape data
- Load: Output analysis‑ready datasets to `data/interim/`

## Data Source & Licensing
- Data source: [Office for National Statistics](https://www.ons.gov.uk)
- Data licence: Crown copyright, Open Government Licence v3.0
- Code licence: MIT License (see `LICENSE` file)

## Contact
### Project Maintainer
- Name: Casey Bell  
- Email: casey.bell.7@outlook.com  
- LinkedIn: [linkedin.com/in/casey-bell](https://linkedin.com/in/casey-bell)

### Official Data Enquiries
- Office for National Statistics  
- Email: pop.info@ons.gov.uk

## Contributing
This project follows standard data science best practices:
- Raw data is kept immutable in `data/raw/`
- All data processing is scripted and reproducible
- Intermediate data outputs are stored separately
- Dependencies are explicitly managed
