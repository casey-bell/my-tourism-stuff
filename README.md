# My Tourism Stuff
A data analysis project.

## Overview
This repository contains a data pipeline and analysis of overseas residents’ visits to Great Britain. The project processes official statistics from the Office for National Statistics (ONS) to analyse trends in visitor numbers, expenditure, and nights stayed from 2019–2024.

## Project Structure
```text
my-tourism-stuff/
├── data/
│   └── raw/
│       └── overseas-visitors-to-britain-2024.xlsx
├── notebooks/
│   └── 01-ingest-and-clean.ipynb
├── src/
│   └── (utility functions for analysis)
├── Makefile
├── pyproject.toml
├── README.md
├── LICENSE
└── .gitignore
```

## Dataset
- Source file: `/data/raw/overseas-visitors-to-britain-2024.xlsx`

### Key Features
- Quarterly data from Q1 2019 to Q4 2024
- Coverage: UK (2019–2023) → Great Britain (2024 onwards)
- Metrics: number of visits, expenditure (£ millions), nights stayed
- Breakdowns by:
  - Geographic region (North America, Europe, Other Countries)
  - Purpose of visit (Holiday, Business, VFR, Miscellaneous)
  - Mode of transport (Air, Sea and Tunnel)
  - UK regions visited
  - Individual countries of residence

### Important Notes
- Methodological break: data from 2024 onwards covers Great Britain only (excluding Northern Ireland), while 2019–2023 data covers the entire UK
- Official statistics in development: these estimates are labelled as developmental as methodologies are being refined

## Usage
### Quick start
```bash
# Install dependencies
pip install -e .

# Run the full data pipeline
make all
```

### Manual execution
- Run the Jupyter notebook: `notebooks/01-ingest-and-clean.ipynb`
- This processes raw data from `/data/raw/` and outputs cleaned datasets

## Use cases
- Tourism trend analysis and visualisation
- Regional economic impact studies
- Seasonal pattern identification
- Market research by country of origin

## Data source
Office for National Statistics, licensed under the Open Government Licence v3.0.

- ONS: https://www.ons.gov.uk
- OGL v3.0: https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/

## Development
- Dependencies are managed via `pyproject.toml`
- Data processing pipeline automated with `Makefile`
- Raw data is kept separate from processed outputs

## Contact
- Repository maintainer: Casey Bell  
  Email: mailto:casey.bell.7@outlook.com  
  LinkedIn: https://linkedin.com/in/casey-bell

- Official data enquiries: Office for National Statistics  
  Email: mailto:pop.info@ons.gov.uk

## Licence
- Code: MIT License (see `LICENSE` file)
- Data: Crown copyright, Open Government Licence v3.0
