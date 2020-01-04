from .census import load_census_block_data
from .logger import logger
from .org_units import get_org_units
from .paths import get_county_data_path


def download_county(county) -> None:

    logger.info("Loading Census block data")
    blocks = load_census_block_data(county)

    logger.info("Clustering into org units")
    blocks = get_org_units(blocks)

    # Write output
    county_path = get_county_data_path(county)
    org_units_shapefile_name = county_path / f"{county.name}_orgunits.shp"
    org_units_csv_name = county_path / f"{county.name}_orgunits.csv"
    blocks.to_file(org_units_shapefile_name)
    blocks.drop(["geometry"], axis=1).to_csv(org_units_csv_name, index=False)

    # write metdatada
    with open(county_path / "README.txt", "w") as meta:
        meta.write(
            """Organizational Voting Units.
    These are Census blocks that are majority black and have at least 50 black households (BHH).
    Adjacent census blocks with fewer than 50 BHH are aggregated together until 100 BHH are found.

    Data dictionary:
        'RandomID' - Randomized org unit ID
        'OrgType' - Org type (block or block aggregate)
        'Precinct' - Precinct number
        'BlackHH' - Estimated Black HH
        'Total_census_population' - Total census population
        'Total_census_Black_population' - Total census Black population
        'Pct_Black_census' - --% Black pop (census)
        'Total_Black_registered_population' - Total Black registered population
        'square_miles' - Area of unit in square miles
        'MECE1' - # of black voters in MECE1
        'MECE2' - # of black voters in MECE2
        'MECE3' - # of black voters in MECE3
        'MECE4' - # of black voters in MECE4
        'MECE5' - # of black voters in MECE5
        'city' - City in which majority of org unit is found
        'support_volunteer_name' -
        'support_vol_phone' -
        'support_vol_email' -
        'block_team_member' -
        'block_team-phone', -
        'block_team_email' -
        'Notes'  -

        """
        )
    logger.info("    Org units saved to {orgunits_shapefile_filename}")
