"""
Data processing for SolarMap AI (adapted to your dataset columns).
- Keep only active connections (CON_STATUS = "In Service")
- Clean numeric fields
- Standardize LOAD to kW
"""

import os
import pandas as pd
import numpy as np

RAW = os.path.join("data", "raw", "hackathon.csv")
CLEAN = os.path.join("data", "processed", "cleaned.csv")
os.makedirs(os.path.dirname(CLEAN), exist_ok=True)


def load_raw(path=RAW):
    return pd.read_csv(path)


def filter_active(df):
    """Keep only active connections (In Service)."""
    if "CON_STATUS" in df.columns:
        df = df[df["CON_STATUS"].astype(str).str.strip().str.lower() == "in service"]
    return df


def clean_numeric(df):
    numeric_cols = [
        "CONSUMPTION_KWH",
        "LOAD",
        "BILLED_AMOUNT",
        "CONSUMPTION_PREV_MNTH",
        "CONSUMPTION_PREV_TO_PREV_MNTH",
        "NO_OF_AC",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df.loc[df[col] < 0, col] = np.nan
            df[col].fillna(df[col].median(), inplace=True)

    # Standardize LOAD: assume >50 means HP → convert to kW
    if "LOAD" in df.columns:
        df["LOAD"] = df["LOAD"].apply(lambda x: x * 0.746 if x > 50 else x)

    # Round coordinates
    df["LAT"] = df["LAT"].round(6)
    df["LON"] = df["LON"].round(6)
    df = df.dropna(subset=['LAT', 'LON'])

    radians_coords = np.radians(df[['LAT', 'LON']].values)

    keep_cols = [
        "SDO_CODE",
        "LAT",
        "LON",
        "CONSUMPTION_KWH",
        "BILLED_AMOUNT",
        "LOAD",
        "NO_OF_AC",
        "CONSUMPTION_PREV_MNTH",
        "CONSUMPTION_PREV_TO_PREV_MNTH",
        "CON_STATUS",
    ]
    df = df[[c for c in keep_cols if c in df.columns]]

    return df


if __name__ == "__main__":
    print("🔹 Loading raw data...")
    df = load_raw()
    print("🔹 Filtering active (In Service) connections...")
    df = filter_active(df)
    print("🔹 Cleaning numeric fields...")
    df = clean_numeric(df)
    df.to_csv(CLEAN, index=False)
    print(f"✅ Cleaned data saved to {CLEAN}")
