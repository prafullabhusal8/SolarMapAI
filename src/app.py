import streamlit as st
import os
import pandas as pd
from utils import make_folium_map, save_map
import joblib # Import joblib to load the cluster summary

st.set_page_config(layout='wide', page_title='SolarMap AI')

st.title("SolarMap AI — Residential Solar Potential")

GEO = os.path.join('outputs', 'clusters.geojson')
MAP_HTML = os.path.join('outputs', 'map.html')
CLEAN = os.path.join('data', 'processed', 'cleaned.csv')
CLUSTER_SUMMARY = os.path.join('outputs', 'cluster_summary.pkl') # Path to cluster summary

st.sidebar.header("Filters / Info")
if os.path.exists(CLEAN):
    df = pd.read_csv(CLEAN)
    st.sidebar.write("Cleaned rows:", len(df))
    
    # Existing district filter
    if 'DISTRICT' in df.columns:
        districts = sorted(df['DISTRICT'].dropna().unique())
        sel = st.sidebar.multiselect("Select district(s) to focus", districts)
        if sel:
            st.write("Showing selected districts:", sel)
            st.dataframe(df[df['DISTRICT'].isin(sel)].head(50))

# --- NEW INTERACTIVE FILTERS ---
if os.path.exists(CLUSTER_SUMMARY):
    cluster_summary = joblib.load(CLUSTER_SUMMARY)
    
    # Convert list of dictionaries to a DataFrame for easier filtering
    summary_df = pd.DataFrame(cluster_summary)

    # Sliders for filtering
    min_units, max_units = st.sidebar.slider(
        "Filter by Avg Monthly Consumption (kWh)",
        float(summary_df['avg_units'].min()), float(summary_df['avg_units'].max()),
        (float(summary_df['avg_units'].min()), float(summary_df['avg_units'].max()))
    )
    
    min_kw, max_kw = st.sidebar.slider(
        "Filter by Suggested Solar Size (kW)",
        float(summary_df['suggested_kw'].min()), float(summary_df['suggested_kw'].max()),
        (float(summary_df['suggested_kw'].min()), float(summary_df['suggested_kw'].max()))
    )

    # Filter the summary based on user selections
    filtered_summary = summary_df[
        (summary_df['avg_units'] >= min_units) & 
        (summary_df['avg_units'] <= max_units) &
        (summary_df['suggested_kw'] >= min_kw) & 
        (summary_df['suggested_kw'] <= max_kw)
    ]
    
    # Generate a temporary GeoJSON with the filtered data
    filtered_geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    for _, row in filtered_summary.iterrows():
        feature = {
            "type": "Feature",
            "properties": row.to_dict(),
            "geometry": {"type": "Point", "coordinates": row["centroid"]}
        }
        filtered_geojson['features'].append(feature)

    # Save the filtered GeoJSON to a temporary file
    temp_geojson_path = os.path.join('outputs', 'filtered_clusters.geojson')
    with open(temp_geojson_path, 'w') as f:
        import json
        json.dump(filtered_geojson, f, indent=2)

    # Render the map using the filtered data
    m = make_folium_map(temp_geojson_path, start_coords=[20.0, 78.0], zoom_start=6)
    save_map(m, path=MAP_HTML)
    
    # Embed the map
    with open(MAP_HTML, 'r', encoding='utf-8') as f:
        html = f.read()
    st.components.v1.html(html, height=650, scrolling=True)

else:
    st.sidebar.info("Cleaned data or cluster summary not found. Run src/data_processing.py and src/clustering.py")

# Original map rendering logic (if clusters.geojson exists but summary doesn't)
if os.path.exists(GEO) and not os.path.exists(CLUSTER_SUMMARY):
    m = make_folium_map(GEO, start_coords=[20.0,78.0], zoom_start=6)
    save_map(m, path=MAP_HTML)
    with open(MAP_HTML, 'r', encoding='utf-8') as f:
        html = f.read()
    st.components.v1.html(html, height=650, scrolling=True)
