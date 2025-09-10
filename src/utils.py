import folium
import json
from folium.plugins import MarkerCluster

def make_folium_map(cluster_geojson_path, start_coords=[20.0, 78.0], zoom_start=6):
    m = folium.Map(location=start_coords, zoom_start=zoom_start, tiles="CartoDB positron")

    with open(cluster_geojson_path, "r") as f:
        gj = json.load(f)

    marker_cluster = MarkerCluster().add_to(m)

    for feat in gj["features"]:
        props = feat["properties"]
        lon, lat = feat["geometry"]["coordinates"]

        tooltip = (
            f"Cluster: {props['cluster']}<br>"
            f"Connections: {props['count']}<br>"
            f"Avg Units: {props['avg_units']:.1f} kWh<br>"
            f"Avg Bill: ₹{props['avg_bill']:.1f}<br>"
            f"Avg Load: {props['avg_load']:.2f} kW<br>"
            f"Avg ACs: {props['avg_acs']:.1f}<br>"
            f"Suggested Solar: {props['suggested_kw']:.2f} kW<br>"
            f"Trend: {props['trend_pct']:.1f}% (vs last month)"
        )

        folium.CircleMarker(
            location=(lat, lon),
            radius=6 + props["count"] ** 0.3,
            color="crimson",
            fill=True,
            fill_opacity=0.7,
            popup=tooltip,
        ).add_to(marker_cluster)

    return m


def save_map(folium_map, path):
    """
    Save a Folium map object to an HTML file.
    
    Parameters:
        folium_map : folium.Map
            The Folium map object to save.
        filepath : str
            The path to the HTML file where the map will be saved.
    """
    folium_map.save(path)
