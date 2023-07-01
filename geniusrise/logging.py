import logging

import colorlog

from geniusrise.config import LOGLEVEL


def setup_logger():
    """Return a logger with a default ColoredFormatter."""
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s "
        "%(yellow)s[%(asctime)s] "
        "%(blue)s[%(name)s:%(lineno)d] "
        "%(green)s%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        reset=True,
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )

    logger = logging.getLogger("geniusrise-cli")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(LOGLEVEL)

    return logger
