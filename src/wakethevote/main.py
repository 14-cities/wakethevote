import os

from . import DATA_PATH


STATES_DATA_PATH = DATA_PATH / "states"


def download_county(county):
    STATE_PATH = STATES_DATA_PATH / county.state
    COUNTY_PATH = STATE_PATH / county.name
    try:
        os.mkdir(STATE_PATH)
    except FileExistsError:
        pass
    try:
        os.mkdir(COUNTY_PATH)
    except FileExistsError:
        pass
