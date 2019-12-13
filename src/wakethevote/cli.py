import argparse
import logging

from .counties import find_counties
from .logger import logger
from .main import download_county
from .preview import preview_county


def main() -> None:
    """
    Command line interface for this repo, try `$ wakevote --help` after install
    """
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
    parser.add_argument("--preview", help="See preview in browser", action="store_true")
    args = parser.parse_args()
    logger.setLevel(args.loglevel)

    for selection in args.selections:
        for county in find_counties(selection):
            if args.preview:
                preview_county(county)
            else:
                logger.info(
                    f"*** Downloading data for {county.name} {county.state} ({county.fips}) ***"
                )
                download_county(county)


if __name__ == "__main__":
    main()
