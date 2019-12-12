import pandas as pd

from . import DATA_PATH

__all__ = ("find_counties",)


FIPS_CSV_PATH = DATA_PATH / "fips.csv"


fips = None


def get_fips():
    global fips
    if fips is None:
        with open(FIPS_CSV_PATH) as fips_csv:
            fips = pd.read_csv(
                fips_csv, sep="\t", usecols=("fips", "name", "state"), dtype=str,
            )
    return fips.copy()


def find_counties(text):
    """Given a bit of text (FIP code, name, etc), yield all the matching counties"""
    counties = get_fips()

    for component in text.split():

        # State (either 2 digit FIP or 2 letter state abbreviation)
        if len(component) == 2:
            if component.isnumeric():
                counties = counties[counties.fips.str.startswith(component)]
            else:
                counties = counties[counties.state == component.upper()]

        # Counties
        else:
            if component.isnumeric():
                counties = counties[counties.fips == component]
            else:
                counties = counties[counties.name == component]

    yield from counties.reset_index().itertuples()
