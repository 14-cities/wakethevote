__version__ = "0.1.0"
from pathlib import Path
import logging


DATA_PATH = Path(__file__).resolve().parents[2] / "data"


logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
