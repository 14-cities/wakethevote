import argparse
import logging

# Load environment variables from a local .env file if one exists
# in a production environment, dotenv would not be installed and environement
# variables would be set a different way
try:
    from dotenv import load_dotenv, find_dotenv
except ModuleNotFoundError:
    pass
else:
    load_dotenv(find_dotenv())

from . import logger
from .counties import find_counties
from .main import download_county


def main():
    parser = argparse.ArgumentParser("WakeVoter")
    parser.add_argument(
        "selections", nargs="+", type=str, help="One or more US States or Counties",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        const=logging.DEBUG,
        default=logging.INFO,
        help="Enable more verbose logging",
        nargs="?",
    )
    args = parser.parse_args()
    logger.setLevel(args.loglevel)

    for selection in args.selections:
        counties = find_counties(selection)
        for county in counties:
            logger.info(
                f"Downloading data for {county.name} {county.state} ({county.fip})"
            )
            download_county(county)


if __name__ == "__main__":
    main()
