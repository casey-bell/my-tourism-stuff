from pathlib import Path
import pandas as pd
from src.data.load import load_table_1
from src.data.clean import clean, DEFAULT_INPUT, DEFAULT_OUTPUT
from src.data.transform import harmonise_columns, normalise_quarter_label, annotate_coverage

# Paths
QUARTERLY_OUTPUT = Path("data/interim/visitors_by_quarter.csv")

def make_visitors_by_quarter():
    """Generate quarterly visitors CSV using the full src pipeline."""
    
    print("🔄 Starting visitors_by_quarter generation...")
    
    # 1) Load the raw data using your specialized function
    print("📥 Loading raw data...")
    df = load_table_1()
    
    if df.empty:
        raise ValueError("Failed to load Table 1 data")
    
    # 2) Select and rename columns for our specific use case
    df = df.rename(columns={
        "Period": "period",
        "World total": "visits"
    })
    df = df[["period", "visits"]].copy()
    
    # 3) Use transform module functions for standardization
    print("🔧 Applying data transformation...")
    df = harmonise_columns(df)
    
    # Normalize quarter labels using transform function
    df["quarter"] = df["period"].apply(normalise_quarter_label)
    
    # Extract year from normalized quarter
    df["year"] = df["quarter"].str.extract(r"(\d{4})")[0].astype("Int64")
    
    # Add coverage annotation (UK vs GB)
    df = annotate_coverage(df)
    
    # 4) Clean numeric values
    df["visits"] = pd.to_numeric(df["visits"], errors="coerce")
    
    # 5) Filter for quarterly data only (exclude annual totals)
    quarterly_mask = df["period"].astype(str).str.contains("Q", na=False)
    df_quarterly = df[quarterly_mask].copy()
    
    # 6) Create period_q in the desired format
    df_quarterly["period_q"] = (
        df_quarterly["year"].astype(str) + " Q" + 
        df_quarterly["quarter"].str.extract(r"Q(\d)")[0]
    )
    
    # 7) Select, sort, and rename final columns
    visitors_by_quarter = df_quarterly[[
        "year", "quarter", "period_q", "visits", "coverage"
    ]].rename(columns={"visits": "visits_thousands"})
    
    visitors_by_quarter = visitors_by_quarter.sort_values(["year", "quarter"]).reset_index(drop=True)
    visitors_by_quarter = visitors_by_quarter.dropna(subset=["visits_thousands"])
    
    # 8) Write CSV
    QUARTERLY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    visitors_by_quarter.to_csv(QUARTERLY_OUTPUT, index=False)
    
    # Print summary
    print(f"✅ Successfully wrote {QUARTERLY_OUTPUT}")
    print(f"📊 Found {len(visitors_by_quarter)} quarters of data")
    print(f"📅 Date range: {visitors_by_quarter['period_q'].min()} to {visitors_by_quarter['period_q'].max()}")
    print(f"🌍 Coverage: {visitors_by_quarter['coverage'].value_counts().to_dict()}")
    print(f"🔢 Total visits (thousands): {visitors_by_quarter['visits_thousands'].sum():,.0f}")
    
    return visitors_by_quarter

def make_visitors_by_quarter_from_clean():
    """Alternative: Generate from fully cleaned dataset."""
    
    print("🔄 Starting from cleaned data...")
    
    # Run cleaning if needed
    if not DEFAULT_OUTPUT.exists():
        print("🧹 Running data cleaning pipeline...")
        clean(DEFAULT_INPUT, DEFAULT_OUTPUT)
    
    # Load cleaned data
    df_clean = pd.read_parquet(DEFAULT_OUTPUT)
    
    # Filter for world total quarterly data
    quarterly_totals = df_clean[
        df_clean["period"].astype(str).str.contains("Q", na=False) & 
        df_clean["visits"].notna()
    ].copy()
    
    # If we have regional breakdowns, we need to identify world totals
    if "region" in quarterly_totals.columns:
        # Look for world total markers
        world_indicators = ["World", "World Total", "Total World", "All Regions"]
        world_mask = quarterly_totals["region"].isin(world_indicators)
        
        if world_mask.any():
            quarterly_totals = quarterly_totals[world_mask]
        else:
            # If no world indicator, take rows where region is missing or assume first occurrence
            quarterly_totals = quarterly_totals[quarterly_totals["region"].isna()].head(1)
    
    # Select and format final output
    visitors_by_quarter = quarterly_totals[[
        "year", "quarter", "period_q", "visits", "coverage"
    ]].rename(columns={"visits": "visits_thousands"})
    
    visitors_by_quarter = visitors_by_quarter.sort_values(["year", "quarter"]).reset_index(drop=True)
    
    # Write output
    QUARTERLY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    visitors_by_quarter.to_csv(QUARTERLY_OUTPUT, index=False)
    
    print(f"✅ Successfully wrote {QUARTERLY_OUTPUT}")
    return visitors_by_quarter

if __name__ == "__main__":
    # Use the direct method (faster) or the clean method (more comprehensive)
    result = make_visitors_by_quarter()
    # result = make_visitors_by_quarter_from_clean()  # Alternative approach
