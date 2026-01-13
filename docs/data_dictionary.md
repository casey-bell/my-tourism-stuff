# Data Dictionary (Processed Layer)

This document defines the schema for the **processed** datasets used in this project. Update as new fields are added during ETL and feature engineering.

## Datasets
- **tourism_kpis.parquet** — region-level monthly KPIs
- **tourism_geo.parquet** — geospatially enriched KPIs (includes geometry)

## Fields (common)
| Field Name           | Data Type | Description                                      |
|----------------------|-----------|--------------------------------------------------|
| date                 | date      | Month start (ISO, e.g., 2024-01-01)             |
| period               | string    | Period label (e.g., "2024M01", "2024Q1")        |
| region_code          | string    | ONS code (e.g., E06000057 for LAD)              |
| region_name          | string    | Human-readable region/LAD name                  |
| nation               | string    | England, Scotland, Wales, Northern Ireland      |
| visitors_total       | integer   | Total number of visitors                        |
| spend_gbp_mn         | float     | Tourism spend in GBP millions                   |
| spend_per_visitor    | float     | Average spend per visitor (GBP)                 |
| accom_occupancy_pct  | float     | Accommodation occupancy percentage              |
| events_index         | float     | Event intensity index (scaled 0–1)              |
| weather_temp_c       | float     | Average temperature (°C)                        |
| weather_precip_mm    | float     | Total precipitation (mm)                        |
| source_version       | string    | Source dataset/version identifier               |

## Geospatial-only fields (in `tourism_geo.parquet`)
| Field Name | Data Type | Description |
|------------|-----------|-------------|
| lad_code   | string    | Local Authority District code (if applicable) |
| geometry   | geometry  | Polygon/shape in EPSG:4326 |

## Constraints & Rules
- **date** must be valid ISO dates; missing dates are not permitted in processed outputs.
- **region_code** must conform to latest ONS coding standards.
- **visitors_total** and **spend_gbp_mn** must be non-negative.
- **accom_occupancy_pct** must be within [0, 100].
- **events_index** is normalised to [0, 1].

## Missing Data Handling
- Use ETL rules to impute or drop: document all imputations in notebook/script comments.
- Prefer forward-fill for short gaps in monthly series; avoid creating artificial trends.

## Provenance
- Track original sources and licenses in `docs/sources_catalog.md`.
- Record `source_version` after each fetch/refresh.
