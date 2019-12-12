import argparse

# Load environment variables from a local .env file if one exists
# in a production environment, dotenv would not be installed and environement
# variables would be set a different way
try:
    from dotenv import load_dotenv, find_dotenv
except ModuleNotFoundError:
    pass
else:
    load_dotenv(find_dotenv())

from .counties import find_counties
from .main import download_county


def main():
    parser = argparse.ArgumentParser("WakeVoter")
    parser.add_argument(
        "selections", nargs="+", type=str, help="One or more US States or Counties",
    )
    args = parser.parse_args()

    for selection in args.selections:
        counties = find_counties(selection)
        for county in counties:
            download_county(county)


if __name__ == "__main__":
    main()
