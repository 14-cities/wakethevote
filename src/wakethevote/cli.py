import argparse
import logging

from . import logger
from .counties import find_counties
from .main import download_county
from .types import County


def main() -> None:
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
        for county in find_counties(selection):
            logger.info(
                f"Downloading data for {county.name} {county.state} ({county.fips})"
            )
            download_county(county)


if __name__ == "__main__":
    main()
