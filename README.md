# Tourism Analytics

A reproducible analytics and forecasting repository for UK tourism trends: visitor volumes, spend, accommodation, attractions, and regional patterns.

## ✨ Features
- Robust ETL and data validation
- Geospatial enrichment (LAD/region joins)
- Time-series forecasting (monthly/quarterly)
- Automated CI for linting, tests, and notebook execution
- Clear documentation (data dictionary & source catalog)

## 🏗️ Project structure
See the folder tree in the root for details on `data/`, `src/`, and `notebooks/`.

## 🚀 Quickstart
```bash
# Create environment
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Pre-commit hooks
pre-commit install

# Run ETL and build features
python scripts/fetch_data.py
python scripts/run_etl.py
python scripts/build_features.py

# Run tests
pytest -q
