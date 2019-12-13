import webbrowser

import folium
import geopandas as gpd

from .logger import logger
from .paths import get_county_data_path
from .types import County


def preview_county(county: County) -> None:
    # Get data folder for counties
    logger.info("Generating HTML preview for {county.name} {county.state}")

    county_path = get_county_data_path(county)

    shapefile_name = county_path / f"{county.name}_orgunits.shp"
    logger.debug(f" - Reading shapefile from {shapefile_name}")
    org_units = gpd.read_file(shapefile_name)

    # Get centroid
    centroid = org_units.unary_union.centroid

    # Convert to JSON
    units_json = org_units.to_json()

    # Convert to folium layers
    lyrUnits = folium.GeoJson(units_json, name="Org Units")

    # Create the map
    m = folium.Map(location=[centroid.y, centroid.x], zoom_start=11)

    # Add the JSON to the map
    lyrUnits.add_to(m)

    # Save the map
    map_file_name = county_path / f"{county.name}_preview.html"
    logger.debug(f" - Saving HTML map file to {map_file_name}")
    m.save(str(map_file_name))

    webbrowser.open(f"file://{map_file_name}")
