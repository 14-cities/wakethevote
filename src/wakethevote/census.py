import os
from datetime import datetime

import geopandas as gpd
import pandas as pd
import requests

from . import logger
from .paths import get_census_data_path, get_county_data_path
from .types import County, CountyFips, StateFips

# Load environment variables from a local .env file if one exists
# in a production environment, dotenv would not be installed and environement
# variables would be set a different way
try:
    from dotenv import load_dotenv, find_dotenv
except ModuleNotFoundError:
    pass
else:
    load_dotenv(find_dotenv())


def load_census_block_data(county: County) -> gpd.GeoDataFrame:
    """Imports census block features for the supplied county FIPS code

    Description:
        Extracts 2010 census block features for the provided county into a
        geodataframe, retrieves race composition attributes, and then joins
        these attributes (population, black population, population 18+,
        black population 18+, and percentages) to the blocks.

        Census feature data are from 'https://www2.census.gov/geo/tiger/'.

    Args:
        county(tuple): County
        state_path(str): path to statewide data
        county_path(str): path to county specific data

    Returns:
        Geodataframe of census blocks for the county with race data
    """
    api_key: str = os.getenv("CENSUS_API_KEY", "")
    assert api_key, "CENSUS_API_KEY environment variable is not defined"

    state_fips = StateFips(county.fips[:2])
    county_fips = CountyFips(county.fips[2:])

    county_path = get_county_data_path(county)

    county_block_file = county_path / f"{county.name}_blocks.shp"

    # See if the data have already been pulled; if so, read into dataframe and return
    if os.path.exists(county_block_file):
        logger.info(f" Census data loaded from {county_block_file}")
        return gpd.read_file(county_block_file)

    logger.debug(f" Failed to load data from {county_block_file}")

    # URL for Census data if we need it
    url = f"https://www2.census.gov/geo/tiger/TIGER2010BLKPOPHU/tabblock2010_{state_fips}_pophu.zip"

    # See if the statewide block shapefile has been downloaded
    census_path = get_census_data_path(county.state)

    state_blocks_file = census_path / "StateBlocks.shp"
    if os.path.exists(state_blocks_file):
        logger.debug(f"  - Loading blocks from {state_blocks_file}")
        state_blocks = gpd.read_file(state_blocks_file)

    # Pull the state block data for the supplied FIPS code
    else:
        logger.info(
            f" - Downloading blocks for state FIPS {state_fips} to "
            f"{state_blocks_file}; this take a few minutes..."
        )
        state_blocks = gpd.read_file(url)
        state_blocks.to_file(state_blocks_file)

    # Subset county blocks
    logger.debug(f"  - Subsetting data for County FIPS {county_fips}")
    county_blocks = state_blocks[state_blocks.COUNTYFP10 == county_fips]

    # Retrieve block attribute data
    logger.debug("  - Fetching block attribute data")
    block_attribues = get_block_attributes(state_fips, county_fips, api_key)
    county_blocks = pd.merge(
        left=county_blocks,
        left_on="BLOCKID10",
        right=block_attribues,
        right_on="GEOID10",
        how="outer",
    )

    # Add field for number of black households
    county_blocks["BlackHH"] = round(  # type: ignore
        county_blocks.HOUSING10 * county_blocks.PctBlack / 100
    ).astype("int")

    # Otherwise, save to a file
    logger.debug(f"  - Saving to {county_block_file}")
    county_blocks.to_file(county_block_file, filetype="Shapefile")

    # Write projection to .prj file
    with open(county_block_file.with_suffix(".prj"), "w") as f:
        f.write(
            'GEOGCS["GCS_North_American_1983",'
            'DATUM["D_North_American_1983",'
            'SPHEROID["GRS_1980",6378137.0,298.257222101]],'
            'PRIMEM["Greenwich",0.0],'
            'UNIT["Degree",0.0174532925199433]]'
        )

    # Write metadata  to .txt file
    current_date = datetime.now().strftime("%Y-%m-%d")
    with open(county_block_file.with_suffix(".txt"), "w") as out_text:
        out_text.write(
            f"Census block data for FIPS {state_fips}{county_fips} extracted from\n"
            f"{url}\n"
            f"on {current_date}.\n\n"
        )
        out_text.write(
            "The following attributes were collected from\n"
            "https://api.census.gov/data/2010/dec/sf1 and joined:\n"
            "\tP003001 - Total population\n"
            "\tP003003 - Total Black or African American population\n"
            "\tP010001 - Total population 18 years and older\n"
            "\tP010004 - Total Black/African-American population 18 years or older\n\n"
        )
        out_text.write("[PctBlack] computed as [P003003] / [P003001] * 100)\n")
        out_text.write("[PctBlack18] computed as [P010004] / [P010001] * 100)\n")
        out_text.write(
            "[BlackHH] computed as [HOUSING10] * [PctBlack]), rounded to the nearest integer"
        )

    return county_blocks


def get_block_attributes(
    state_fips: StateFips, county_fips: CountyFips, api_key: str
) -> gpd.GeoDataFrame:
    """Retrieves race composition data using the Census API

    Description: Pulls the following block level data from the 2010 SF1 file:
        P003001 - Total population
        P003003 - Total Black or African American population
        P010001 - Total population 18 years and older
        P010004 - Total Black/African-American population 18 years or older
    Then compute pct Black and pct Black (18+) columns along with

    Args:
        state_fips(str): State FIPS code (e.g. '37')
        county_fips(str): County FIPS code (e.g. '183')
        api_key(str): Census API key

    Returns:
        geodataframe of census blocks for the county
    """
    # Census API call to get the data for the provided state/county
    url = "https://api.census.gov/data/2010/dec/sf1"
    params = {
        "get": "P003001,P003003,P010001,P010004",
        "for": "block:*",
        "in": f"state:{state_fips}%county:{county_fips}",
        "key": api_key,
    }
    # Send the request and convert the response to JSON format
    logger.info(f"   ...downloading data from {url}")
    response = requests.get(url, params)

    # Handle empty response
    if not response.content:
        raise requests.exceptions.RequestException(
            f"Unexpected empty response from {url} with parameters {params}"
        )

    response_json = response.json()
    # Convert JSON to pandas dataframe
    logger.debug("   ...cleaning census racial data...")
    data = pd.DataFrame(response_json[1:], columns=response_json[0])
    # Convert block data columns to numeric
    floatColumns = ["P003001", "P003003", "P010001", "P010004"]
    data[floatColumns] = data[floatColumns].apply(pd.to_numeric)
    # Combine columns into single GEOID10 attribute
    data["GEOID10"] = data.state + data.county + data.tract + data.block
    # Compute percentages
    data["PctBlack"] = data.P003003 / data.P003001 * 100
    data["PctBlack18"] = data.P010004 / data.P010001 * 100

    # Set null values to zero
    data.fillna(0, inplace=True)
    # Remove GEOID component columns
    data.drop(["state", "county", "tract", "block"], axis="columns", inplace=True)

    return data
