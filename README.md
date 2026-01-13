# Tourism Analytics

A reproducible analytics and forecasting repository for tourism trends: visitor volumes, spend, accommodation, attractions, and regional patterns.

## ✨ Features
- Robust ETL and data validation
- Geospatial enrichment (LAD/region joins)
- Time-series forecasting (monthly/quarterly)
- Automated CI for linting, tests, and notebook execution
- Clear documentation (data dictionary & source catalogue)

## 🏗️ Project Structure
```
my-tourism-stuff/
├─ data/              # raw, interim, processed datasets
├─ docs/              # documentation and data dictionary
├─ notebooks/         # Jupyter notebooks for analysis
├─ src/               # source code for ETL, modeling, visualisation
├─ scripts/           # automation scripts for ETL and modeling
├─ tests/             # unit tests
```

## 🚀 Quickstart
```bash
# 1. Create virtual environment
python -m venv .venv && source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install pre-commit hooks
pre-commit install

# 4. Run ETL and feature engineering
python scripts/fetch_data.py
python scripts/run_etl.py
python scripts/build_features.py

# 5. Run tests
pytest -q
```

## 📚 Documentation
- [Data Dictionary](docs/data_dictionary.md)
- [Sources Catalogue](docs/sources_catalogue.md)

## 🔐 Licensing
- Code: MIT License
- Data: Refer to `/docs/sources_catalogue.md`

## 🧭 Governance
- Branch protection and PR reviews
- Versioned data with DVC
