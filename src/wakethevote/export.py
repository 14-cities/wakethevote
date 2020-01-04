from collections import defaultdict
from typing import Iterable

import geopandas as gpd
import pandas as pd

from .logger import logger
from .paths import STATES_DATA_PATH, get_county_data_path
from .types import County


def export_counties(counties: Iterable[County]) -> None:
    """
    Load saved county data and export as a single GeoJSON file
    """

    logger.info(f"Exporting selected data to GeoJSON file(s)")

    shapefiles = defaultdict(list)
    for county in counties:
        logger.debug(f"** Loading data for {county.name}, {county.state}")
        county_path = get_county_data_path(county)
        org_units_shapefile_name = county_path / f"{county.name}_orgunits.shp"
        try:
            shapefiles[county.state].append(gpd.read_file(org_units_shapefile_name))

        # Reading a file that doesn't exist will raise an child of ValueError
        except ValueError as e:
            logger.warning(e)

    for state, counties in shapefiles.items():
        export_file_path = STATES_DATA_PATH / state / f"{state}_shapes.json"
        logger.debug(f"* Saving export to {export_file_path}")

        gdf = pd.concat([c for c in counties]).pipe(gpd.GeoDataFrame)
        gdf.to_file(export_file_path, driver="GeoJSON")
