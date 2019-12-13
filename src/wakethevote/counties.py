from typing import Iterator

import pandas as pd

from .logger import logger
from .paths import FIPS_TSV_PATH
from .types import County

__all__ = ("find_counties",)


fips = None


def get_fips() -> pd.DataFrame:
    """Get a copy of the fips data"""
    global fips
    if fips is None:
        with open(FIPS_TSV_PATH) as fips_csv:
            fips = pd.read_csv(
                fips_csv, sep="\t", usecols=("fips", "name", "state"), dtype=str,
            )
    return fips.copy()


def find_counties(text: str) -> Iterator[County]:
    """Given a bit of text (FIP code, name, etc), yield all the matching counties"""
    counties = get_fips()

    logger.debug(f"* Finding Counties that match {text}: ")
    for component in text.split():

        # State (either 2 digit FIP or 2 letter state abbreviation)
        if len(component) == 2:
            if component.isnumeric():
                logger.debug(f"  - Filtering for state FIPS {component}")
                counties = counties[counties.fips.str.startswith(component)]
            else:
                logger.debug(f"  - Filtering for state name {component}")
                counties = counties[counties.state == component.upper()]

        # Counties
        else:
            if component.isnumeric():
                logger.debug(f"  - Filtering for county FIPS {component}")
                counties = counties[counties.fips == component]
            else:
                logger.debug(f"  - Filtering for county name {component}")
                counties = counties[counties.name == component]

    yield from counties.reset_index().itertuples(index=False, name="County")
