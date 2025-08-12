import streamlit as st
import geopandas as gpd
import pandas as pd
from shapely.validation import make_valid
import leafmap.foliumap as leafmap

st.set_page_config(page_title="Geometry Checker", layout="wide")
st.title("🗺 Geometry Checker: Layer Rules Validation")

layer1_file = st.file_uploader("Upload Layer 1 (main layer)", type=["zip", "geojson", "gpkg"])
layer2_file = st.file_uploader("Upload Layer 2 (reference layer)", type=["zip", "geojson", "gpkg"])

if layer1_file and layer2_file:
    gdf1 = gpd.read_file(layer1_file).to_crs(epsg=4326)
    gdf2 = gpd.read_file(layer2_file).to_crs(epsg=4326)

    st.subheader("Rule 1: No duplicates in Layer 1")
    duplicates = gdf1[gdf1.duplicated(subset=["geometry"])]
    if not duplicates.empty:
        st.error(f"Found {len(duplicates)} duplicate geometries.")
    else:
        st.success("✅ No duplicates found.")

    st.subheader("Rule 2: No gaps in Layer 1")
    union_geom = gdf1.unary_union
    bounds_poly = union_geom.convex_hull
    gaps = bounds_poly.difference(union_geom)
    if not gaps.is_empty:
        st.error("Found gaps in Layer 1 coverage.")
    else:
        st.success("✅ No gaps detected.")

    st.subheader("Rule 3: No invalid geometries in Layer 1")
    invalid = gdf1[~gdf1.is_valid]
    if not invalid.empty:
        st.error(f"Found {len(invalid)} invalid geometries.")
        if st.button("Fix Invalid Geometries"):
            gdf1["geometry"] = gdf1["geometry"].apply(make_valid)
            st.success("Invalid geometries fixed.")
    else:
        st.success("✅ All geometries are valid.")

    st.subheader("Rule 4: No overlaps in Layer 1")
    overlaps = []
    for idx, geom in gdf1.iterrows():
        others = gdf1.drop(idx)
        for _, other in others.iterrows():
            if geom.geometry.intersects(other.geometry) and not geom.geometry.touches(other.geometry):
                overlaps.append((idx, other.name))
    if overlaps:
        st.error(f"Found {len(overlaps)} overlaps within Layer 1.")
    else:
        st.success("✅ No overlaps within Layer 1.")

    st.subheader("Rule 5: No overlaps between Layer 1 and Layer 2")
    inter = gpd.overlay(gdf1, gdf2, how='intersection')
    if not inter.empty:
        st.error(f"Found {len(inter)} overlaps between Layer 1 and Layer 2.")
    else:
        st.success("✅ No overlaps with Layer 2.")

    st.subheader("Map View")
    m = leafmap.Map(center=[9, 8], zoom=6)
    m.add_gdf(gdf1, "Layer 1")
    m.add_gdf(gdf2, "Layer 2")
    if not duplicates.empty:
        m.add_gdf(duplicates, "Duplicates", color="red")
    if not gaps.is_empty:
        m.add_gdf(gpd.GeoDataFrame(geometry=[gaps], crs="EPSG:4326"), "Gaps", color="orange")
    if not inter.empty:
        m.add_gdf(inter, "Intersections", color="purple")
    m.to_streamlit(height=500)
