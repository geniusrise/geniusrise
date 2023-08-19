# 🧠 Geniusrise
# Copyright (C) 2023  geniusrise.ai
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging

import colorlog

from geniusrise.config import LOGLEVEL


# def setup_logger() -> logging.Logger:
#     logging.basicConfig(level=logging.DEBUG)
#     logger = logging.getLogger("geniusrise")
#     return logger


def setup_logger() -> logging.Logger:
    """
    🛠️ **Setup Logger**: Configure and return a logger with a default ColoredFormatter.

    This function sets up a logger for the `geniusrise-cli` with colorful logging outputs. The log level is determined by the `LOGLEVEL` from the configuration.

    ## Usage:
    ```python
    logger = setup_logger()
    logger.info("This is a fancy info log!")
    ```

    Returns:
        logging.Logger: Configured logger with colorful outputs.
    """
    # Reset all existing loggers
    for logger in logging.root.manager.loggerDict.values():
        if isinstance(logger, logging.Logger):
            logger.setLevel(logging.NOTSET)
            for handler in logger.handlers.copy():
                logger.removeHandler(handler)

    # Define the custom formatter
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

    # Setup logger for geniusrise
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("geniusrise")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.getLevelName(LOGLEVEL))

    return logger
