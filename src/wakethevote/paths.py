from pathlib import Path

from .types import County

DATA_PATH = Path(__file__).resolve().parents[2] / "data"
FIPS_TSV_PATH = DATA_PATH / "fips.tsv"
STATES_DATA_PATH = DATA_PATH / "states"


def get_census_data_path(state: str):
    path = STATES_DATA_PATH / state / "census"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_county_data_path(county: County) -> Path:
    path = STATES_DATA_PATH / county.state / "counties" / county.name
    path.mkdir(parents=True, exist_ok=True)
    return path
