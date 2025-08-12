import streamlit as st
import geopandas as gpd
from shapely.ops import unary_union
from shapely.validation import make_valid
import leafmap.foliumap as leafmap

st.set_page_config(page_title="Polygon Geometry Checker", layout="wide")

st.title("🗺 Polygon Geometry Checker & Fixer")
st.markdown("Upload two or more polygon datasets to check for overlaps, intersections, and invalid geometries.")

uploaded_files = st.file_uploader(
    "Upload polygon files (Shapefile ZIP, GeoJSON, KML, GPKG)",
    type=["zip", "geojson", "kml", "gpkg"],
    accept_multiple_files=True
)

if uploaded_files:
    gdfs = []
    for file in uploaded_files:
        gdf = gpd.read_file(file)
        gdf = gdf.to_crs(epsg=4326)  # Standardize CRS
        gdfs.append(gdf)

    # Merge into single GeoDataFrame for analysis
    all_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs="EPSG:4326")

    st.subheader("Geometry Validation")
    invalid_geoms = all_gdf[~all_gdf.is_valid]
    if not invalid_geoms.empty:
        st.error(f"Found {len(invalid_geoms)} invalid geometries.")
        fix = st.button("Fix Invalid Geometries")
        if fix:
            all_gdf["geometry"] = all_gdf["geometry"].apply(make_valid)
            st.success("Invalid geometries fixed.")
    else:
        st.success("✅ No invalid geometries found.")

    # Detect overlaps/intersections
    st.subheader("Overlaps & Intersections")
    overlaps = []
    for i, row in all_gdf.iterrows():
        others = all_gdf.drop(i)
        for _, other in others.iterrows():
            if row.geometry.intersects(other.geometry) and not row.geometry.touches(other.geometry):
                overlaps.append((i, other.name))
    if overlaps:
        st.warning(f"Found {len(overlaps)} overlaps/intersections.")
    else:
        st.success("✅ No overlaps or intersections detected.")

    # Map visualization
    st.subheader("Map View")
    m = leafmap.Map(center=[9.0820, 8.6753], zoom=6)
    m.add_gdf(all_gdf, layer_name="Polygons")
    m.to_streamlit(width=900, height=500)

    # Download fixed dataset
    if st.button("Download Cleaned File"):
        output_path = "cleaned_polygons.geojson"
        all_gdf.to_file(output_path, driver="GeoJSON")
        with open(output_path, "rb") as f:
            st.download_button("Download GeoJSON", f, file_name="cleaned_polygons.geojson")
