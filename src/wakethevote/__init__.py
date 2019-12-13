__version__ = "0.1.0"
import logging

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
