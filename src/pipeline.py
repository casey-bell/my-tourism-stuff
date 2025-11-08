import sys
from pathlib import Path

# Adjust path to enable imports from project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd  # noqa: E402

from src.data.load import load_table_1  # noqa: E402
from src.data.clean import clean, DEFAULT_INPUT, DEFAULT_OUTPUT  # noqa: E402
from src.data.transform import (  # noqa: E402
    harmonise_columns,
    normalise_quarter_label,
    annotate_coverage,
)

# Paths
QUARTERLY_OUTPUT = (
    project_root / "data" / "interim" / "visitors_by_quarter.csv"
)


def make_visitors_by_quarter():
    """Generate quarterly visitors CSV using the full src pipeline."""
    print("🔄 Starting visitors_by_quarter generation...")

    # 1) Load the raw data using the specialized function
    print("📥 Loading raw data...")
    df = load_table_1()

    if df.empty:
        raise ValueError("Failed to load Table 1 data")

    # 2) Select and rename columns for our specific use case
    df = df.rename(columns={"Period": "period", "World total": "visits"})
    df = df[["period", "visits"]].copy()

    # 3) Use transform module functions for standardization
    print("🔧 Applying data transformation...")
    df = harmonise_columns(df)

    # Normalize quarter labels using transform function
    df["quarter"] = df["period"].astype(str).apply(normalise_quarter_label)

    # Extract year from normalized quarter
    df["year"] = (
        df["quarter"].astype(str).str.extract(r"(\d{4})")[0]
        .astype("Int64")
    )

    # Add coverage annotation (UK vs GB, etc.)
    df = annotate_coverage(df)

    # 4) Clean numeric values
    df["visits"] = pd.to_numeric(df["visits"], errors="coerce")

    # 5) Filter for quarterly data only (exclude annual totals)
    quarterly_mask = df["period"].astype(str).str.contains("Q", na=False)
    df_quarterly = df[quarterly_mask].copy()

    if df_quarterly.empty:
        print("⚠️ No quarterly rows found after filtering.")
        # still write an empty CSV with headers so downstream steps don't fail
        QUARTERLY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(
            columns=[
                "year",
                "quarter",
                "period_q",
                "visits_thousands",
                "coverage",
            ]
        ).to_csv(QUARTERLY_OUTPUT, index=False)
        return pd.DataFrame()

    # 6) Create period_q in the desired format
    quarter_num = (
        df_quarterly["quarter"].astype(str).str.extract(r"Q(\d)")[0]
    )
    df_quarterly["period_q"] = (
        df_quarterly["year"].astype(str) + " Q" + quarter_num
    )

    # 7) Select, sort, and rename final columns
    visitors_by_quarter = df_quarterly[
        ["year", "quarter", "period_q", "visits", "coverage"]
    ].rename(columns={"visits": "visits_thousands"})

    visitors_by_quarter = visitors_by_quarter.sort_values(
        ["year", "quarter"]
    ).reset_index(drop=True)

    visitors_by_quarter = visitors_by_quarter.dropna(
        subset=["visits_thousands"]
    )

    # 8) Write CSV
    QUARTERLY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    visitors_by_quarter.to_csv(QUARTERLY_OUTPUT, index=False)

    # Print summary (keep lines short for linting)
    print(f"✅ Wrote {QUARTERLY_OUTPUT}")
    print(f"📊 Rows: {len(visitors_by_quarter)}")
    if not visitors_by_quarter.empty:
        print(
            "📅 Date range: "
            f"{visitors_by_quarter['period_q'].min()} to "
            f"{visitors_by_quarter['period_q'].max()}"
        )
        print(
            "🌍 Coverage: "
            f"{visitors_by_quarter['coverage'].value_counts().to_dict()}"
        )
        total_visits = visitors_by_quarter["visits_thousands"].sum(skipna=True)
        print(f"🔢 Total visits (thousands): {total_visits:,.0f}")

    return visitors_by_quarter


def make_visitors_by_quarter_from_clean():
    """Alternative: Generate output from fully cleaned dataset."""
    print("🔄 Starting from cleaned data...")

    # Run cleaning if needed
    if not DEFAULT_OUTPUT.exists():
        print("🧹 Running data cleaning pipeline...")
        clean(DEFAULT_INPUT, DEFAULT_OUTPUT)

    # Load cleaned data
    df_clean = pd.read_parquet(DEFAULT_OUTPUT)

    # Filter for world total quarterly data
    quarterly_totals = df_clean[
        df_clean["period"].astype(str).str.contains("Q", na=False)
        & df_clean["visits"].notna()
    ].copy()

    # If we have regional breakdowns, identify world totals
    if "region" in quarterly_totals.columns:
        world_indicators = [
            "World",
            "World Total",
            "Total World",
            "All Regions",
        ]
        world_mask = quarterly_totals["region"].isin(world_indicators)

        if world_mask.any():
            quarterly_totals = quarterly_totals[world_mask]
        else:
            quarterly_totals = quarterly_totals[
                quarterly_totals["region"].isna()
            ].head(1)

    # Select and format final output
    visitors_by_quarter = quarterly_totals[
        ["year", "quarter", "period_q", "visits", "coverage"]
    ].rename(columns={"visits": "visits_thousands"})

    visitors_by_quarter = visitors_by_quarter.sort_values(
        ["year", "quarter"]
    ).reset_index(drop=True)

    # Write output
    QUARTERLY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    visitors_by_quarter.to_csv(QUARTERLY_OUTPUT, index=False)

    print(f"✅ Wrote {QUARTERLY_OUTPUT}")
    return visitors_by_quarter


if __name__ == "__main__":
    # Default: use the direct method (faster).
    make_visitors_by_quarter()
