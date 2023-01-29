import logging

logger = logging.getLogger("ComMU")
logger.setLevel(logging.ERROR)
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.handlers = []
logger.propagate = False
logger.addHandler(handler)
