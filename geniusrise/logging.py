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
from typing import Any, Optional

import colorlog
from geniusrise.core.state import State

from geniusrise.config import LOGLEVEL


class StateHandler(logging.Handler):
    """
    🛠️ **StateHandler**: Handler for logging state changes.

    This class is used to capture logging via state module in geniusrise.
    """

    def __init__(self, state_instance: State):
        super().__init__()
        self.state = state_instance

    def emit(self, record: Any):
        log_entry = self.format(record)
        self.state.capture_log(log_entry)


def setup_logger(state_instance: Optional[State] = None) -> logging.Logger:
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
    formatter = (
        colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)-8s%(reset)s "
            "%(yellow)s[%(asctime)s] "
            "%(blue)s[%(name)s:%(lineno)d] "
            "%(log_color)s%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            reset=True,
            log_colors={
                "DEBUG": "white",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )
        if logging.getLevelName(LOGLEVEL) < logging.INFO
        else colorlog.ColoredFormatter(
            "%(log_color)-8s%(reset)s %(log_color)s%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            reset=True,
            log_colors={
                "DEBUG": "white",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )
    )

    # Suppress kafka library info logs
    if logging.getLevelName(LOGLEVEL) < logging.INFO:
        logger = logging.getLogger("kafka")
        logger.setLevel(logging.WARN)

    # Setup logger for geniusrise
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    if state_instance:
        state_handler = StateHandler(state_instance)
        state_handler.setFormatter(formatter)

    logging.basicConfig(encoding="utf-8", level=logging.getLevelName(LOGLEVEL), handlers=[handler])
    logger = logging.getLogger("geniusrise")
    logger.setLevel(logging.getLevelName(LOGLEVEL))

    return logger
