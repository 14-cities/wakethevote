import os

from . import DATA_PATH, logger
from .census import load_census_data


STATES_DATA_PATH = DATA_PATH / "states"


def download_county(county) -> None:
    STATE_PATH = STATES_DATA_PATH / county.state

    blocks = load_census_data(county, STATE_PATH)
    print(blocks)
