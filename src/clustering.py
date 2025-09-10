"""
Clustering active consumers into spatial groups and computing cluster metrics.
Adds Avg AC count and Consumption Trend %.
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
import joblib

CLEAN = os.path.join("data", "processed", "cleaned.csv")
OUT_GEO = os.path.join("outputs", "clusters.geojson")
OUT_SUM = os.path.join("outputs", "cluster_summary.pkl")
os.makedirs(os.path.dirname(OUT_GEO), exist_ok=True)


def dbscan_haversine(df, eps_meters=500, min_samples=10):
    coords = df[["LAT", "LON"]].to_numpy()
    radians_coords = np.radians(coords)
    eps = eps_meters / 6371000.0  # Earth radius in meters
    model = DBSCAN(eps=eps, min_samples=min_samples, metric="haversine")
    labels = model.fit_predict(radians_coords)
    df["cluster"] = labels
    return df, model


def compute_summary(df):
    groups = df[df["cluster"] >= 0].groupby("cluster")
    summary = []

    for cid, g in groups:
        avg_units = float(g["CONSUMPTION_KWH"].mean())
        avg_bill = float(g["BILLED_AMOUNT"].mean()) if "BILLED_AMOUNT" in g else None
        avg_load = float(g["LOAD"].mean()) if "LOAD" in g else None
        avg_acs = float(g["NO_OF_AC"].mean()) if "NO_OF_AC" in g else None

        # Suggested system size = monthly units / (30 days * 4 hrs avg sun)
        suggested_kw = avg_units / (30 * 4) if avg_units > 0 else 0.0

        # Consumption trend %
        if "CONSUMPTION_PREV_MNTH" in g and "CONSUMPTION_PREV_TO_PREV_MNTH" in g:
            prev = g["CONSUMPTION_PREV_MNTH"].mean()
            prev2 = g["CONSUMPTION_PREV_TO_PREV_MNTH"].mean()
            trend = ((prev - prev2) / prev2 * 100) if prev2 > 0 else 0.0
        else:
            trend = None

        centroid_lat = float(g["LAT"].mean())
        centroid_lon = float(g["LON"].mean())

        summary.append(
            {
                "cluster": int(cid),
                "count": int(len(g)),
                "avg_units": avg_units,
                "avg_bill": avg_bill,
                "avg_load": avg_load,
                "avg_acs": avg_acs,
                "suggested_kw": suggested_kw,
                "trend_pct": trend,
                "centroid": [centroid_lon, centroid_lat],
            }
        )
    return summary


def to_geojson(summary):
    features = []
    for s in summary:
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "cluster": s["cluster"],
                    "count": s["count"],
                    "avg_units": s["avg_units"],
                    "avg_bill": s["avg_bill"],
                    "avg_load": s["avg_load"],
                    "avg_acs": s["avg_acs"],
                    "suggested_kw": s["suggested_kw"],
                    "trend_pct": s["trend_pct"],
                },
                "geometry": {"type": "Point", "coordinates": s["centroid"]},
            }
        )
    return {"type": "FeatureCollection", "features": features}


if __name__ == "__main__":
    print("🔹 Loading cleaned data...")
    df = pd.read_csv(CLEAN)

    print("🔹 Running DBSCAN clustering...")
    df, model = dbscan_haversine(df)

    print("🔹 Computing cluster summary...")
    summary = compute_summary(df)
    geojson = to_geojson(summary)

    with open(OUT_GEO, "w") as f:
        json.dump(geojson, f, indent=2)

    joblib.dump(summary, OUT_SUM)
    print(f"✅ Saved clusters to {OUT_GEO}")
