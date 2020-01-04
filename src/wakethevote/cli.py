import argparse
import logging
import sys
from itertools import chain

from .counties import find_counties
from .download import download_county
from .export import export_counties
from .logger import logger
from .preview import preview_county


def main() -> None:
    """
    Command line interface for this repo, try `$ wakevote --help` after install
    """
    parser = argparse.ArgumentParser(
        "WakeVoter",
        description="Must include one of the following: --download, --preview, or --export",
    )
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

    # Must choose one of these three options
    parser.add_argument(
        "--download", help="Download county level data", action="store_true"
    )
    parser.add_argument(
        "--preview", help="See a preview in browser", action="store_true"
    )
    parser.add_argument(
        "--export",
        help="Export all data for a state as a GeoJSON file",
        action="store_true",
    )

    args = parser.parse_args()
    logger.setLevel(args.loglevel)

    mutually_exclusive_required_args = (args.download, args.preview, args.export)
    if len([arg for arg in mutually_exclusive_required_args if arg]) != 1:
        sys.exit(
            f"{parser.prog}: error: you must choose one (and only one) of the "
            "following flags --download, --preview, or --export"
        )

    counties = chain.from_iterable(find_counties(s) for s in args.selections)

    if args.preview:
        for county in counties:
            preview_county(county)

    elif args.download:
        for county in counties:
            download_county(county)

    elif args.export:
        export_counties(counties)


if __name__ == "__main__":
    main()
